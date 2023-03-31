import typing
from dataclasses import dataclass

from shvatka.core.interfaces.dal.level_times import GameStatDao
from shvatka.core.models import dto

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class GameStatImpl(GameStatDao):
    dao: "HolderDao"

    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        return await self.dao.level_time.get_game_level_times(game)

    async def get_max_level_number(self, game: dto.Game) -> int:
        return await self.dao.level.get_max_level_number(game)

    async def get_by_player(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return await self.dao.organizer.get_by_player(game=game, player=player)

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        return await self.dao.organizer.get_by_player_or_none(game=game, player=player)
