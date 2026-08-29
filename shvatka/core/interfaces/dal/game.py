from datetime import datetime
from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.file_info import FileInfoGetter, FileUpserter
from shvatka.core.interfaces.dal.file_link import FileIdsByGuidsGetter, LevelFilesSyncDao
from shvatka.core.interfaces.dal.level import LevelUpserter
from shvatka.core.models import dto
from shvatka.core.models.dto import hints, scn


class GameNameChecker(Protocol):
    async def is_name_available(self, name: str) -> bool:
        raise NotImplementedError


class MaxGameNumberGetter(Protocol):
    async def get_max_number(self) -> int:
        raise NotImplementedError


class GameNumberUpdater(Protocol):
    async def set_number(self, game: dto.Game, number: int) -> None:
        raise NotImplementedError


class GameStatusCompleter(Protocol):
    async def set_completed(self, game: dto.Game) -> None:
        raise NotImplementedError


class GameUpserter(LevelUpserter, GameNameChecker, Protocol):
    async def upsert_game(self, author: dto.Player, scenario: scn.GameScenario) -> dto.Game:
        raise NotImplementedError

    async def upsert_file(self, file: hints.FileMeta, author: dto.Player) -> hints.SavedFileMeta:
        raise NotImplementedError

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        raise NotImplementedError

    async def is_author_game_by_name(self, name: str, author: dto.Player) -> bool:
        raise NotImplementedError

    async def get_game_by_name(self, name: str, author: dto.Player) -> dto.Game:
        raise NotImplementedError


class GameCreator(Committer, GameNameChecker, LevelFilesSyncDao, Protocol):
    async def create_game(self, author: dto.Player, name: str) -> dto.Game:
        raise NotImplementedError

    async def link_to_game(self, level: dto.Level, game: dto.Game) -> dto.GamedLevel:
        raise NotImplementedError


class GameRenamer(Committer, Protocol):
    async def rename_game(self, game: dto.Game, new_name: str):
        raise NotImplementedError


class GameAuthorTransferer(Protocol):
    async def transfer(self, game: dto.Game, new_author: dto.Player) -> None:
        raise NotImplementedError


class GameAuthorsFinder(Committer, Protocol):
    async def get_all_by_author(self, author: dto.Player) -> list[dto.Game]:
        raise NotImplementedError


class PreviewGameByIdGetter(Protocol):
    async def get_preview(self, id_: int, author: dto.Player | None = None) -> dto.PreviewGame:
        raise NotImplementedError


class GameByIdGetter(Protocol):
    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        raise NotImplementedError

    async def get_full(self, id_: int) -> dto.FullGame:
        raise NotImplementedError

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        raise NotImplementedError


class GameFileUploader(GameByIdGetter, FileUpserter, Protocol):
    async def add_game_file(self, game_id: int, file_id: int) -> None:
        raise NotImplementedError


class GameFileRenamer(GameByIdGetter, Committer, Protocol):
    async def is_game_file(self, game_id: int, guid: str) -> bool:
        raise NotImplementedError

    async def rename_file(self, guid: str, filename: str) -> None:
        raise NotImplementedError

    async def get_by_guid(self, guid: str) -> hints.VerifiableFileMeta:
        raise NotImplementedError


class GameFileDeleter(GameByIdGetter, FileInfoGetter, FileIdsByGuidsGetter, Committer, Protocol):
    """Reads and writes the deletion of one file from one game needs.

    Everything a file can still be referenced by has a reader here: the levels
    of the game, the releases of every game, and the remaining links of any
    kind. Which of them make a file undeletable — and when the file itself may
    follow its last link — is the interactor's call, not the DAO's.
    """

    async def get_game_file_ids(self, game_id: int) -> set[int]:
        raise NotImplementedError

    async def get_release_guids(self) -> dict[int, set[str]]:
        raise NotImplementedError

    async def get_level_ids_using_file(self, game_id: int, file_id: int) -> set[int]:
        raise NotImplementedError

    async def delete_game_file_link(self, game_id: int, file_id: int) -> None:
        raise NotImplementedError

    async def count_links_for_file(self, file_id: int) -> int:
        """How many ``game_files`` and ``level_files`` rows point at the file."""
        raise NotImplementedError

    async def delete_file_meta(self, guid: str) -> None:
        raise NotImplementedError

    async def count_metas_with_path(self, file_path: str) -> int:
        raise NotImplementedError


class GameReleaseGetter(Protocol):
    async def get_release(self, game_id: int) -> dto.GameRelease | None:
        raise NotImplementedError


class GameReleaseSaver(Committer, GameReleaseGetter, Protocol):
    async def save_release(
        self, game: dto.Game, banner: hints.PhotoHint | None, hints_: list[hints.AnyHint]
    ) -> None:
        raise NotImplementedError

    async def delete_release(self, game: dto.Game) -> None:
        raise NotImplementedError


class ActiveGameFinder(Protocol):
    async def get_active_game(self) -> dto.Game | None:
        raise NotImplementedError


class WaiverStarter(Committer, ActiveGameFinder, Protocol):
    async def start_waivers(self, game: dto.Game) -> None:
        raise NotImplementedError


class GameStartPlanner(Committer, ActiveGameFinder, Protocol):
    async def set_start_at(self, game: dto.Game, start_at: datetime) -> None:
        raise NotImplementedError

    async def cancel_start(self, game: dto.Game):
        raise NotImplementedError


class CompletedGameFinder(Protocol):
    async def get_completed_games(self) -> list[dto.Game]:
        raise NotImplementedError


class GameAuthorMerger(Protocol):
    async def replace_games_author(self, primary: dto.Player, secondary: dto.Player) -> None:
        raise NotImplementedError
