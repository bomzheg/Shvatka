from dataclasses import dataclass

from db.dao import GameDao, LevelDao, FileInfoDao
from shvatka.dal.game import GameUpserter, GameCreator
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

    async def is_name_available(self, name: str) -> bool:
        return await self.game.is_name_available(name)

    async def is_author_game_by_name(self, name: str, author: dto.Player) -> bool:
        return await self.game.is_author_game_by_name(name, author)

    async def commit(self):
        await self.level.commit()


@dataclass
class GameCreatorImpl(GameCreator):
    game: GameDao
    level: LevelDao

    async def create_game(self, author: dto.Player, name: str) -> dto.Game:
        return await self.game.create_game(author, name)

    async def link_to_game(self, level: dto.Level, game: dto.Game) -> dto.Level:
        return await self.level.link_to_game(level, game)

    async def commit(self) -> None:
        return await self.game.commit()

    async def is_name_available(self, name: str) -> bool:
        return await self.game.is_name_available(name)
