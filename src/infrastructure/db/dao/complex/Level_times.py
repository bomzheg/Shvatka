from dataclasses import dataclass

from src.infrastructure.db.dao import LevelTimeDao, LevelDao, OrganizerDao
from src.shvatka.interfaces.dal.level_times import GameStatDao
from src.shvatka.models import dto


@dataclass
class GameStatImpl(GameStatDao):
    level_times: LevelTimeDao
    level: LevelDao
    organizer: OrganizerDao

    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        return await self.level_times.get_game_level_times(game)

    async def get_max_level_number(self, game: dto.Game) -> int:
        return await self.level.get_max_level_number(game)

    async def get_by_player(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return await self.organizer.get_by_player(game=game, player=player)

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        return await self.organizer.get_by_player_or_none(game=game, player=player)
