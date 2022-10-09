from abc import ABCMeta
from typing import Iterable

from shvatka.dal.base import Committer, Reader
from shvatka.models import dto


class GameStarter(Committer, metaclass=ABCMeta):
    async def set_game_started(self, game: dto.Game) -> None:
        raise NotImplementedError

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def set_teams_to_first_level(self, game: dto.Game, teams: Iterable[dto.Team]) -> None:
        raise NotImplementedError


class LevelTimeChecker(Reader):
    async def is_team_on_level(self, team: dto.Team, level: dto.Level) -> bool:
        raise NotImplementedError
