from dataclasses import dataclass

from shvatka.core.interfaces.dal.game import GameUpserter, GameCreator, GamePackager
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.infrastructure.db.dao import GameDao, LevelDao, FileInfoDao


@dataclass
class GameUpserterImpl(GameUpserter):
    game: GameDao
    level: LevelDao
    file_info: FileInfoDao

    async def upsert_game(self, author: dto.Player, scenario: scn.GameScenario) -> dto.Game:
        return await self.game.upsert_game(author, scenario)

    async def upsert(
        self,
        author: dto.Player,
        scenario: scn.LevelScenario,
        game: dto.Game = None,
        no_in_game: int = None,
    ) -> dto.Level:
        return await self.level.upsert(author, scenario, game, no_in_game)

    async def unlink_all(self, game: dto.Game) -> None:
        return await self.level.unlink_all(game)

    async def upsert_file(self, file: scn.FileMeta, author: dto.Player) -> scn.SavedFileMeta:
        return await self.file_info.upsert(file, author)

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        return await self.file_info.check_author_can_own_guid(author, guid)

    async def is_name_available(self, name: str) -> bool:
        return await self.game.is_name_available(name)

    async def is_author_game_by_name(self, name: str, author: dto.Player) -> bool:
        return await self.game.is_author_game_by_name(name, author)

    async def get_game_by_name(self, name: str, author: dto.Player) -> dto.Game:
        return await self.game.get_game_by_name(name=name, author=author)

    async def commit(self) -> None:
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


@dataclass
class GamePackagerImpl(GamePackager):
    game: GameDao
    file_info: FileInfoDao

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.game.get_full(id_)

    async def get_by_guid(self, guid: str) -> scn.VerifiableFileMeta:
        return await self.file_info.get_by_guid(guid)
