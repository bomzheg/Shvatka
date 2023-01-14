from typing import Iterable, Protocol

from shvatka.interfaces.dal.base import Committer
from shvatka.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.models import dto


class GameStarter(Protocol, Committer):
    async def set_game_started(self, game: dto.Game) -> None:
        raise NotImplementedError

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def set_teams_to_first_level(self, game: dto.Game, teams: Iterable[dto.Team]) -> None:
        raise NotImplementedError


class LevelTimeChecker(Protocol):
    async def is_team_on_level(self, team: dto.Team, level: dto.Level) -> bool:
        raise NotImplementedError


class GameStatDao(Protocol, OrgByPlayerGetter):
    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        raise NotImplementedError

    async def get_max_level_number(self, game: dto.Game) -> int:
        raise NotImplementedError
