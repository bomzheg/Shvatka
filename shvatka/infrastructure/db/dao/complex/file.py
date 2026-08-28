"""Single-adapter views over the tables a file lives in.

``files_info`` describes a file, ``level_files`` and ``game_files`` link it, and
the storage holds its content. Deleting one — or sweeping every file nothing
refers to — reads and writes all of them, so each use case gets one adapter
composing the per-table DAOs it needs.
"""

import typing
from collections.abc import Collection
from dataclasses import dataclass

from shvatka.core.files.adapters import FileGarbageCollectorDao
from shvatka.core.files.dto import GameFileLink
from shvatka.core.interfaces.dal.game import GameFileDeleter
from shvatka.core.models import dto
from shvatka.core.models.dto import hints

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class ReleaseGuidsMixin:
    dao: "HolderDao"

    async def get_release_guids(self) -> dict[int, set[str]]:
        return await self.dao.game.get_release_guids()


@dataclass
class GameFileDeleterImpl(ReleaseGuidsMixin, GameFileDeleter):
    """Single DAO for deleting one file from one game (cdn endpoint)."""

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_, author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        return await self.dao.game.add_levels(game)

    async def get_by_guid(self, guid: str) -> hints.VerifiableFileMeta:
        return await self.dao.file_info.get_by_guid(guid)

    async def get_ids_by_guids(self, guids: Collection[str]) -> list[int]:
        return await self.dao.file_info.get_ids_by_guids(guids)

    async def get_game_file_ids(self, game_id: int) -> set[int]:
        return await self.dao.game_file.get_file_ids(game_id)

    async def get_level_ids_using_file(self, game_id: int, file_id: int) -> set[int]:
        return await self.dao.level_file.get_level_ids_by_file(game_id, file_id)

    async def delete_game_file_link(self, game_id: int, file_id: int) -> None:
        await self.dao.game_file.delete_link(game_id, file_id)

    async def count_links_for_file(self, file_id: int) -> int:
        return await self.dao.game_file.count_for_file(
            file_id
        ) + await self.dao.level_file.count_for_file(file_id)

    async def delete_file_meta(self, guid: str) -> None:
        await self.dao.file_info.delete_by_guid(guid)

    async def count_metas_with_path(self, file_path: str) -> int:
        return await self.dao.file_info.count_by_file_path(file_path)

    async def commit(self) -> None:
        await self.dao.commit()


@dataclass
class FileGarbageCollectorImpl(ReleaseGuidsMixin, FileGarbageCollectorDao):
    """Single DAO for a garbage collection run."""

    async def get_unused_game_file_links(self) -> list[GameFileLink]:
        return await self.dao.game_file.get_unused_links()

    async def get_guids_by_ids(self, file_ids: Collection[int]) -> dict[int, str]:
        return await self.dao.file_info.get_guids_by_ids(file_ids)

    async def delete_game_file_links(self, ids: Collection[int]) -> None:
        await self.dao.game_file.delete_links(ids)

    async def get_unlinked_file_metas(
        self, ignored_game_link_ids: Collection[int] = ()
    ) -> list[hints.VerifiableFileMeta]:
        return await self.dao.file_info.get_unlinked(ignored_game_link_ids)

    async def delete_file_metas(self, guids: Collection[str]) -> None:
        await self.dao.file_info.delete_by_guids(guids)

    async def get_paths_by_guid(self) -> dict[str, str]:
        return await self.dao.file_info.get_paths_by_guid()

    async def commit(self) -> None:
        await self.dao.commit()
