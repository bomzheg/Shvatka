import typing
from dataclasses import dataclass
from typing import Iterable

from shvatka.core.interfaces.dal.complex import GamePackager, GameFileLoader
from shvatka.core.interfaces.dal.game import GameUpserter, GameCreator
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.infrastructure.db.dao import GameDao, LevelDao, FileInfoDao

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


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
        game: dto.Game | None = None,
        no_in_game: int | None = None,
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
    dao: "HolderDao"

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        return await self.dao.waiver.get_played_teams(game)

    async def get_played(self, game: dto.Game, team: dto.Team) -> Iterable[dto.VotedPlayer]:
        return await self.dao.waiver.get_played(game, team)

    async def get_all_by_game(self, game: dto.Game) -> list[dto.Waiver]:
        return await self.dao.waiver.get_all_by_game(game)

    async def get_typed_keys_grouped(self, game: dto.Game) -> dict[dto.Team, list[dto.KeyTime]]:
        return await self.dao.key_time.get_typed_key_grouped(game)

    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        return await self.dao.level_time.get_game_level_times(game)

    async def get_game_level_times_by_teams(
        self, game: dto.Game, levels_count: int
    ) -> dict[dto.Team, list[dto.LevelTimeOnGame]]:
        return await self.dao.level_time.get_game_level_times_by_teams(game, levels_count)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def get_by_guid(self, guid: str) -> scn.VerifiableFileMeta:
        return await self.dao.file_info.get_by_guid(guid)


class GameFilesGetterImpl(GameFileLoader):
    def __init__(self, dao: "HolderDao"):
        self.dao = dao

    async def get_by_guid(self, guid: str) -> scn.VerifiableFileMeta:
        return await self.dao.file_info.get_by_guid(guid)

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_, author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def get_by_user(self, user: dto.User) -> dto.Player:
        return await self.dao.player.get_by_user(user)
