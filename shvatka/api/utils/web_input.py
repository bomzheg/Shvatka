import logging
from dataclasses import dataclass, field
from typing import Iterable

from shvatka.api.utils.push import PushMessage, WebPushSender
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.game_play import GamePreparer
from shvatka.core.models import dto
from shvatka.core.models.dto import action
from shvatka.core.views.game import (
    GameView,
    GameLogWriter,
    GameLogEvent,
    OrgNotifier,
    Event,
    LevelUp,
    NewOrg,
    LevelTestCompleted,
    InputContainer,
    GameViewPreparer,
)
from shvatka.core.views.team import TeamNotifier, TeamEvent

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class WebInput(InputContainer):
    new_key: dto.KeyTime | None = None
    effects: list[action.Effects] = field(default_factory=list)
    game_finished: bool = False


class WebGameView(GameView):
    def __init__(self, push_sender: WebPushSender, current_game: CurrentGameProvider) -> None:
        self.push_sender = push_sender
        self.current_game = current_game

    async def _voted_player_ids(self, team: dto.Team) -> set[int]:
        """Only players who voted yes for the current game should get in-game pushes."""
        waivers = await self.current_game.get_team_waivers_by_team(team)
        return {voted.player.id for voted in waivers}

    async def _send_to_played(self, team: dto.Team, message: PushMessage) -> None:
        await self.push_sender.send_to_players(
            player_ids=await self._voted_player_ids(team),
            message=message,
        )

    async def send_puzzle(self, team: dto.Team, level: dto.Level) -> None:
        await self._send_to_played(
            team,
            PushMessage(
                title="Новый уровень",
                body=f"{team.name}: открыт уровень {self._level_label(level)}",
                url="/games/running",
                tag=f"level-{team.id}-{level.db_id}",
                data={"kind": "puzzle", "team_id": team.id, "level_id": level.db_id},
            ),
        )

    async def send_hint(self, team: dto.Team, hint_number: int, level: dto.Level) -> None:
        await self._send_to_played(
            team,
            PushMessage(
                title="Новая подсказка",
                body=f"{team.name}: подсказка #{hint_number}",
                url="/games/running",
                tag=f"hint-{team.id}-{level.db_id}-{hint_number}",
                data={
                    "kind": "hint",
                    "team_id": team.id,
                    "level_id": level.db_id,
                    "hint_number": hint_number,
                },
            ),
        )

    async def duplicate_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        if isinstance(input_container, WebInput):
            input_container.new_key = key

    async def wrong_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        if isinstance(input_container, WebInput):
            input_container.new_key = key

    async def effects_key(
        self, key: dto.KeyTime, effects: action.Effects, input_container: InputContainer
    ) -> None:
        if isinstance(input_container, WebInput):
            input_container.effects.append(effects)
            input_container.new_key = key

    async def game_finished(self, team: dto.Team, input_container: InputContainer) -> None:
        if isinstance(input_container, WebInput):
            input_container.game_finished = True
        await self._send_to_played(
            team,
            PushMessage(
                title="Финиш!",
                body=f"{team.name}: вы завершили игру",
                url="/games/running",
                tag=f"finish-{team.id}",
                data={"kind": "team_finished", "team_id": team.id},
            ),
        )

    async def game_finished_by_all(self, team: dto.Team) -> None:
        await self._send_to_played(
            team,
            PushMessage(
                title="Игра завершена",
                body="Все завершили игру",
                url="/games/running",
                tag="game-finished",
                data={"kind": "game_finished", "team_id": team.id},
            ),
        )

    async def effects(
        self, team: dto.Team, effects: action.Effects, input_container: InputContainer
    ) -> None:
        if isinstance(input_container, WebInput):
            input_container.effects.append(effects)
        await self._send_to_played(
            team,
            PushMessage(
                title="Событие на уровне",
                body=f"{team.name}: сработал эффект",
                url="/games/running",
                tag=f"effects-{team.id}-{effects.id}",
                data={"kind": "effects", "team_id": team.id, "effects_id": str(effects.id)},
            ),
        )

    @staticmethod
    def _level_label(level: dto.Level) -> int | str:
        if level.number_in_game is None:
            return level.name_id
        return level.number_in_game + 1


class WebGamePreparer(GameViewPreparer):
    async def prepare_game_view(
        self,
        game: dto.Game,
        teams: Iterable[dto.Team],
        orgs: Iterable[dto.Organizer],
        dao: GamePreparer,
    ) -> None:
        pass


class WebGameLogWriter(GameLogWriter):
    async def log(self, log_event: GameLogEvent) -> None:
        pass


class WebOrgNotifier(OrgNotifier):
    def __init__(self, push_sender: WebPushSender) -> None:
        self.push_sender = push_sender

    async def notify(self, event: Event) -> None:
        match event:
            case LevelUp():
                await self._notify_level_up(event)
            case NewOrg():
                await self._notify_new_org(event)
            case LevelTestCompleted():
                await self._notify_level_test_completed(event)
            case _:
                logger.warning("unknown org event %s, no web push sent", type(event))

    async def _notify_orgs(self, event: Event, message: PushMessage) -> None:
        await self.push_sender.send_to_players(
            player_ids={org.player.id for org in event.orgs_list},
            message=message,
        )

    async def _notify_level_up(self, event: LevelUp) -> None:
        await self._notify_orgs(
            event,
            PushMessage(
                title=f"{event.team.name} на {event.new_level.name_id}",
                body=f"Команда {event.team.name} перешла на уровень "
                f"{self._level_label(event.new_level)}",
                url="/games/running",
                tag=f"org-level-up-{event.team.id}-{event.new_level.db_id}",
                data={
                    "kind": "org_level_up",
                    "team_id": event.team.id,
                    "level_id": event.new_level.db_id,
                },
            ),
        )

    async def _notify_new_org(self, event: NewOrg) -> None:
        await self._notify_orgs(
            event,
            PushMessage(
                title=f"Новый орг {event.org.player.name_mention}",
                body=f"На игру {event.game.name} добавлен новый орг "
                f"{event.org.player.name_mention}",
                url="/games/running",
                tag=f"org-new-org-{event.game.id}-{event.org.id}",
                data={
                    "kind": "new_org",
                    "game_id": event.game.id,
                    "org_id": event.org.id,
                },
            ),
        )

    async def _notify_level_test_completed(self, event: LevelTestCompleted) -> None:
        seconds = event.result.td.seconds
        await self._notify_orgs(
            event,
            PushMessage(
                title="Тестирование уровня завершено",
                body=f"Игрок {event.suite.tester.player.name_mention} "
                f"закончил тестирование уровня {event.suite.level.name_id} "
                f"за {seconds // 60} минут {seconds % 60} с.",
                url="/games/running",
                tag=f"org-level-test-{event.suite.level.name_id}",
                data={
                    "kind": "level_test_completed",
                    "level_name_id": event.suite.level.name_id,
                },
            ),
        )

    @staticmethod
    def _level_label(level: dto.Level) -> str:
        if level.number_in_game is None:
            return level.name_id
        return f"{level.number_in_game + 1} ({level.name_id})"


class WebTeamNotifier(TeamNotifier):
    async def notify(self, event: TeamEvent) -> None:
        pass
