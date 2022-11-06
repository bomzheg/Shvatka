from dataclasses import dataclass

from db.dao import GameDao, LevelDao, FileInfoDao
from shvatka.dal.game import GameUpserter
from shvatka.models import dto
from shvatka.models.dto.scn import FileMeta, SavedFileMeta
from shvatka.models.dto.scn.game import GameScenario
from shvatka.models.dto.scn.level import LevelScenario


@dataclass
class GameUpserterImpl(GameUpserter):
    game: GameDao
    level: LevelDao
    file_info: FileInfoDao

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

    async def upsert_file(self, file: FileMeta, author: dto.Player) -> SavedFileMeta:
        return await self.file_info.upsert(file, author)

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        return await self.file_info.check_author_can_own_guid(author, guid)

    async def commit(self):
        await self.level.commit()
