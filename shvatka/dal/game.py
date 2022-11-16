from abc import ABCMeta
from datetime import datetime

from shvatka.dal.base import Committer, Reader
from shvatka.dal.level import LevelUpserter
from shvatka.models import dto
from shvatka.models.dto.scn import FileMeta, SavedFileMeta
from shvatka.models.dto.scn.file_content import VerifiableFileMeta
from shvatka.models.dto.scn.game import GameScenario


class GameNameChecker(Reader):
    async def is_name_available(self, name: str) -> bool:
        raise NotImplementedError


class GameUpserter(LevelUpserter, GameNameChecker, metaclass=ABCMeta):
    async def upsert_game(self, author: dto.Player, scn: GameScenario) -> dto.Game:
        raise NotImplementedError

    async def upsert_file(self, file: FileMeta, author: dto.Player) -> SavedFileMeta:
        raise NotImplementedError

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        raise NotImplementedError

    async def is_author_game_by_name(self, name: str, author: dto.Player) -> bool:
        raise NotImplementedError


class GameCreator(Committer, GameNameChecker, metaclass=ABCMeta):
    async def create_game(self, author: dto.Player, name: str) -> dto.Game:
        raise NotImplementedError

    async def link_to_game(self, level: dto.Level, game: dto.Game) -> dto.Level:
        raise NotImplementedError


class GameRenamer(Committer, metaclass=ABCMeta):
    async def rename_game(self, game: dto.Game, new_name: str):
        raise NotImplementedError


class GameAuthorsFinder(Committer, metaclass=ABCMeta):
    async def get_all_by_author(self, author: dto.Player) -> list[dto.Game]:
        raise NotImplementedError


class GameByIdGetter(Reader, metaclass=ABCMeta):
    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        raise NotImplementedError

    async def get_full(self, id_: int) -> dto.FullGame:
        raise NotImplementedError


class ActiveGameFinder(Reader):
    async def get_active_game(self) -> dto.Game | None:
        raise NotImplementedError


class WaiverStarter(Committer, ActiveGameFinder, metaclass=ABCMeta):
    async def start_waivers(self, game: dto.Game) -> None:
        raise NotImplementedError


class GameStartPlanner(Committer, ActiveGameFinder, metaclass=ABCMeta):
    async def set_start_at(self, game: dto.Game, start_at: datetime) -> None:
        raise NotImplementedError

    async def cancel_start(self, game: dto.Game):
        raise NotImplementedError


class GamePackager(Reader):
    async def get_full(self, id_: int) -> dto.FullGame:
        raise NotImplementedError

    async def get_by_guid(self, guid: str) -> VerifiableFileMeta:
        raise NotImplementedError

