from dataclasses import dataclass

from shvatka.core.games.input import InputContainer
from shvatka.core.models import dto
from shvatka.core.models.dto import action
from shvatka.core.views.game import GameView, GameLogWriter, GameLogEvent, OrgNotifier, Event


@dataclass
class WebInput(InputContainer):
    pass


class WebGameView(GameView):
    async def send_puzzle(self, team: dto.Team, level: dto.Level) -> None:
        pass

    async def send_hint(self, team: dto.Team, hint_number: int, level: dto.Level) -> None:
        pass

    async def duplicate_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        pass

    async def wrong_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        pass

    async def effects_key(self, key: dto.KeyTime, effects: action.Effects, input_container: InputContainer) -> None:
        pass

    async def game_finished(self, team: dto.Team, input_container: InputContainer) -> None:
        pass

    async def game_finished_by_all(self, team: dto.Team) -> None:
        pass

    async def effects(self, team: dto.Team, effects: action.Effects, input_container: InputContainer) -> None:
        pass


class WebGameLogWriter(GameLogWriter):
    async def log(self, log_event: GameLogEvent) -> None:
        pass

class WebOrgNotifier(OrgNotifier):
    async def notify(self, event: Event) -> None:
        pass