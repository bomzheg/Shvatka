from collections.abc import Collection
from typing import Protocol

from shvatka.core.files.dto import GameFileLink
from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models.dto import hints


class ReleaseGuidsGetter(Protocol):
    async def get_release_guids(self) -> dict[int, set[str]]:
        raise NotImplementedError


class FileGarbageCollectorDao(Committer, ReleaseGuidsGetter, Protocol):
    async def get_unused_game_file_links(self) -> list[GameFileLink]:
        raise NotImplementedError

    async def get_guids_by_ids(self, file_ids: Collection[int]) -> dict[int, str]:
        raise NotImplementedError

    async def delete_game_file_links(self, ids: Collection[int]) -> None:
        raise NotImplementedError

    async def get_unlinked_file_metas(
        self, ignored_game_link_ids: Collection[int] = ()
    ) -> list[hints.VerifiableFileMeta]:
        raise NotImplementedError

    async def delete_file_metas(self, guids: Collection[str]) -> None:
        raise NotImplementedError

    async def get_paths_by_guid(self) -> dict[str, str]:
        raise NotImplementedError
