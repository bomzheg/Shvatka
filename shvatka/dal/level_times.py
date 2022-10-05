from abc import ABCMeta
from typing import Iterable

from shvatka.dal.base import Committer
from shvatka.models import dto
from shvatka.models.dto.scn.time_hint import TimeHint


class GameStarter(Committer, metaclass=ABCMeta):
    async def set_game_started(self, game: dto.Game) -> None:
        raise NotImplementedError

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def set_teams_to_first_level(self, game: dto.Game, teams: Iterable[dto.Team]) -> None:
        raise NotImplementedError

    async def get_next_hint(self, game: dto.Game, current_level: int, current_hint: int) -> TimeHint:
        raise NotImplementedError

    async def get_puzzle(self, game: dto.Game, level_number: int) -> TimeHint:
        raise NotImplementedError
