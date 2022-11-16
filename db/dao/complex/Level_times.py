from dataclasses import dataclass

from db.dao import LevelTimeDao, LevelDao
from shvatka.dal.level_times import GameStatDao
from shvatka.models import dto


@dataclass
class GameStatImpl(GameStatDao):
    level_times: LevelTimeDao
    level: LevelDao

    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        return await self.level_times.get_game_level_times(game)

    async def get_max_level_number(self, game: dto.Game) -> int:
        return await self.level.get_max_level_number(game)
