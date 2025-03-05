from typing import Iterable, Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models import dto


class GameStarter(Committer, Protocol):
    async def set_game_started(self, game: dto.Game) -> None:
        raise NotImplementedError

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def set_to_level(
        self,
        team: dto.Team,
        game: dto.Game,
        level_number: int,
    ) -> dto.LevelTime:
        raise NotImplementedError


class LevelTimesGetter(Protocol):
    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        raise NotImplementedError

    async def get_game_level_times_by_teams(
        self, game: dto.Game, levels_count: int
    ) -> dict[dto.Team, list[dto.LevelTime]]:
        raise NotImplementedError

    async def get_game_level_times_with_hints(
        self, game: dto.FullGame
    ) -> dict[dto.Team, list[dto.LevelTimeOnGame]]:
        raise NotImplementedError


class LevelByTeamGetter(Protocol):
    async def get_current_level_time(self, team: dto.Team, game: dto.Game) -> dto.LevelTime:
        raise NotImplementedError


class TeamLevelsMerger(Protocol):
    async def replace_team_levels(self, primary: dto.Team, secondary: dto.Team):
        raise NotImplementedError
