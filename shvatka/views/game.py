from typing import Protocol, Iterable

from shvatka.models import dto
from shvatka.models.dto.scn.time_hint import TimeHint


class GameViewPreparer(Protocol):
    async def prepare_game_view(
        self, game: dto.Game, teams: Iterable[dto.Team], orgs: Iterable[dto.Organizer],
    ):
        pass


class GameView(Protocol):
    async def send_puzzle(self, team: dto.Team, puzzle: TimeHint):
        pass


class GameLogWriter(Protocol):
    async def log(self, message: str): pass


class OrgNotifier(Protocol):
    async def notify(self, event): pass
