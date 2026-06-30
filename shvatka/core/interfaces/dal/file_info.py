from collections.abc import Collection
from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models import dto
from shvatka.core.models.dto import hints


class FileInfoMerger(Protocol):
    async def replace_file_info(self, primary: dto.Player, secondary: dto.Player) -> None:
        raise NotImplementedError


class FileInfoGetter(Protocol):
    async def get_by_guid(self, guid: str) -> hints.VerifiableFileMeta:
        raise NotImplementedError


class GameFilesMetaGetter(Protocol):
    """Reads the files usable in a game (the ``game_files`` table) as metas."""

    async def get_game_file_ids(self, game_id: int) -> set[int]:
        raise NotImplementedError

    async def get_metas_by_ids(self, file_ids: Collection[int]) -> list[hints.VerifiableFileMeta]:
        raise NotImplementedError

    async def get_game_file_metas(self, game_id: int) -> list[hints.VerifiableFileMeta]:
        return await self.get_metas_by_ids(await self.get_game_file_ids(game_id))


class FileUpserter(Committer, Protocol):
    async def upsert(self, file: hints.FileMeta, author: dto.Player) -> hints.SavedFileMeta:
        raise NotImplementedError

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        raise NotImplementedError
