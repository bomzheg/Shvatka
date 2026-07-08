import typing
from dataclasses import dataclass

from shvatka.core.models import dto
from shvatka.core.search.adapters import GlobalSearchDao
from shvatka.core.search.dto import LevelWithGame

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class GlobalSearchDaoImpl(GlobalSearchDao):
    dao: "HolderDao"

    async def search_completed_games(self, text: str) -> list[dto.Game]:
        return await self.dao.game.search_completed(text)

    async def search_levels_of_completed_games(self, text: str) -> list[LevelWithGame]:
        return await self.dao.level.search_in_completed_games(text)

    async def search_teams(self, text: str) -> list[dto.Team]:
        return await self.dao.team.search_by_name(text)

    async def search_players(self, text: str) -> list[dto.Player]:
        return await self.dao.player.search_by_any_name(text)
