from typing import Iterable, Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.core.models import dto


class GameStarter(Committer, Protocol):
    async def set_game_started(self, game: dto.Game) -> None:
        raise NotImplementedError

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def set_teams_to_first_level(self, game: dto.Game, teams: Iterable[dto.Team]) -> None:
        raise NotImplementedError


class LevelTimeChecker(Protocol):
    async def is_team_on_level(self, team: dto.Team, level: dto.Level) -> bool:
        raise NotImplementedError


class GameStatDao(OrgByPlayerGetter, Protocol):
    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        raise NotImplementedError

    async def get_max_level_number(self, game: dto.Game) -> int:
        raise NotImplementedError


class TeamLevelsMerger(Protocol):
    async def replace_team_levels(self, primary: dto.Team, secondary: dto.Team):
        raise NotImplementedError
