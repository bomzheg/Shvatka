from typing import Protocol

from shvatka.core.models import dto
from shvatka.core.search.dto import LevelWithGame


class GlobalSearchDao(Protocol):
    async def search_completed_games(self, text: str) -> list[dto.Game]:
        raise NotImplementedError

    async def search_levels_of_completed_games(self, text: str) -> list[LevelWithGame]:
        raise NotImplementedError

    async def search_teams(self, text: str) -> list[dto.Team]:
        raise NotImplementedError

    async def search_players(self, text: str) -> list[dto.PlayerWithForum]:
        raise NotImplementedError
