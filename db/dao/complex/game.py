from dataclasses import dataclass

from db.dao import GameDao, LevelDao
from shvatka.dal.game import GameUpserter
from shvatka.models import dto
from shvatka.models.dto.scn.game import GameScenario
from shvatka.models.dto.scn.level import LevelScenario


@dataclass
class GameUpserterImpl(GameUpserter):
    game: GameDao
    level: LevelDao

    async def upsert_game(self, author: dto.Player, scn: GameScenario) -> dto.Game:
        return await self.game.upsert_game(author, scn)

    async def upsert(
        self,
        author: dto.Player,
        scn: LevelScenario,
        game: dto.Game = None,
        no_in_game: int = None,
    ) -> dto.Level:
        return await self.level.upsert(author, scn, game, no_in_game)

    async def unlink_all(self, game: dto.Game) -> None:
        return await self.level.unlink_all(game)

    async def commit(self):
        await self.level.commit()
