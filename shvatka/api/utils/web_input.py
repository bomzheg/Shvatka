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
from shvatka.core.interfaces.dal.player import TeamPlayersGetter
from shvatka.core.models.enums.notification import NotificationType, NotificationSeverity
from shvatka.core.notifications.adapters import NotificationWriter
from shvatka.core.views.team import (
    TeamNotifier,
    TeamEvent,
    PlayerJoinedTeam,
    PlayerLeftTeam,
)

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
    def __init__(self, push_sender: WebPushSender, notification_dao: NotificationWriter) -> None:
        self.push_sender = push_sender
        self.notification_dao = notification_dao

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
        recipient_ids = {org.player.id for org in event.orgs_list} | {event.org.player.id}
        try:
            await self.notification_dao.create_for_recipients(
                recipient_ids=recipient_ids,
                type_=NotificationType.org_added,
                severity=NotificationSeverity.normal,
                actor_id=event.org.player.id,
                payload={
                    "game_id": event.game.id,
                    "game_name": event.game.name,
                    "org_id": event.org.id,
                    "org_name": event.org.player.name_mention,
                },
            )
            await self.notification_dao.commit()
        except Exception as e:
            logger.exception("failed to persist org_added notifications", exc_info=e)
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
    def __init__(
        self,
        notification_dao: NotificationWriter,
        team_players_dao: TeamPlayersGetter,
        push_sender: WebPushSender,
    ) -> None:
        self.notification_dao = notification_dao
        self.team_players_dao = team_players_dao
        self.push_sender = push_sender

    async def notify(self, event: TeamEvent) -> None:
        match event:
            case PlayerJoinedTeam():
                await self._notify(event, self._joined_spec(event))
            case PlayerLeftTeam():
                await self._notify(event, self._left_spec(event))
            case _:
                logger.warning("unknown team event %s, no notification persisted", type(event))

    async def _notify(self, event: TeamEvent, spec: "_TeamNotificationSpec") -> None:
        recipient_ids = await self._team_member_ids(event.team)
        if not recipient_ids:
            return
        try:
            await self.notification_dao.create_for_recipients(
                recipient_ids=recipient_ids,
                type_=spec.type,
                severity=spec.severity,
                actor_id=event.actor.id,
                payload=spec.payload,
            )
            await self.notification_dao.commit()
        except Exception as e:
            logger.exception("failed to persist team notifications", exc_info=e)
        await self.push_sender.send_to_players(player_ids=recipient_ids, message=spec.push)

    async def _team_member_ids(self, team: dto.Team) -> set[int]:
        players = await self.team_players_dao.get_players(team)
        return {tp.player.id for tp in players}

    @staticmethod
    def _joined_spec(event: PlayerJoinedTeam) -> "_TeamNotificationSpec":
        payload = {
            "team_id": event.team.id,
            "team_name": event.team.name,
            "player_id": event.invited.id,
            "player_name": event.invited.name_mention,
            "by_self": event.by_self,
        }
        return _TeamNotificationSpec(
            type=NotificationType.player_joined_team,
            severity=NotificationSeverity.low,
            payload=payload,
            push=PushMessage(
                title=f"{event.team.name}: новый игрок",
                body=f"{event.invited.name_mention} вступил в команду",
                url="/teams",
                tag=f"team-join-{event.team.id}-{event.invited.id}",
                data={"kind": "player_joined_team", "team_id": event.team.id},
            ),
        )

    @staticmethod
    def _left_spec(event: PlayerLeftTeam) -> "_TeamNotificationSpec":
        payload = {
            "team_id": event.team.id,
            "team_name": event.team.name,
            "player_id": event.removed.id,
            "player_name": event.removed.name_mention,
            "by_self": event.by_self,
        }
        return _TeamNotificationSpec(
            type=NotificationType.player_left_team,
            severity=NotificationSeverity.normal,
            payload=payload,
            push=PushMessage(
                title=f"{event.team.name}: игрок вышел",
                body=f"{event.removed.name_mention} покинул команду",
                url="/teams",
                tag=f"team-leave-{event.team.id}-{event.removed.id}",
                data={"kind": "player_left_team", "team_id": event.team.id},
            ),
        )


@dataclass(frozen=True, slots=True)
class _TeamNotificationSpec:
    type: NotificationType
    severity: NotificationSeverity
    payload: dict
    push: PushMessage
