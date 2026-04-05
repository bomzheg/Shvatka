from dataclasses import dataclass, field
from typing import Iterable

from shvatka.core.interfaces.dal.game_play import GamePreparer
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import action
from shvatka.core.views.game import (
    GameView,
    GameLogWriter,
    GameLogEvent,
    OrgNotifier,
    Event,
    InputContainer, GameViewPreparer,
)


@dataclass(kw_only=True)
class WebInput(InputContainer):
    new_key: dto.KeyTime | None = None
    effects: list[action.Effects] = field(default_factory=list)
    game_finished: bool = False

    @property
    def wrong_key(self) -> bool:
        return self.new_key.type_ == enums.KeyType.wrong if self.new_key is not None else False

    @property
    def duplicate_key(self) -> bool:
        return self.new_key.is_duplicate if self.new_key is not None else False


class WebGameView(GameView):
    async def send_puzzle(self, team: dto.Team, level: dto.Level) -> None:
        pass

    async def send_hint(self, team: dto.Team, hint_number: int, level: dto.Level) -> None:
        pass

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

    async def game_finished_by_all(self, team: dto.Team) -> None:
        pass

    async def effects(
        self, team: dto.Team, effects: action.Effects, input_container: InputContainer
    ) -> None:
        if isinstance(input_container, WebInput):
            input_container.effects.append(effects)


class WebGamePreparer(GameViewPreparer):

    async def prepare_game_view(self, game: dto.Game, teams: Iterable[dto.Team], orgs: Iterable[dto.Organizer],
                                dao: GamePreparer) -> None:
        pass


class WebGameLogWriter(GameLogWriter):
    async def log(self, log_event: GameLogEvent) -> None:
        pass


class WebOrgNotifier(OrgNotifier):
    async def notify(self, event: Event) -> None:
        pass
