from collections.abc import Collection
from typing import Protocol

from shvatka.core.files.dto import GameFileLink
from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models.dto import hints


class ReleaseGuidsGetter(Protocol):
    async def get_release_guids(self) -> dict[int, set[str]]:
        """guids of the files each game's release refers to, by game id.

        A release is jsonb on the game, not rows in ``level_files``, so nothing
        else records that it uses a file — whoever counts references to a file
        has to read the releases as well.
        """
        raise NotImplementedError


class FileGarbageCollectorDao(Committer, ReleaseGuidsGetter, Protocol):
    """Everything a garbage collection run reads and deletes.

    The DAO only provides the per-table operations; which of them run, and in
    what order, is the interactor's decision.
    """

    async def get_unused_game_file_links(self) -> list[GameFileLink]:
        """``game_files`` rows for files no level of that game refers to."""
        raise NotImplementedError

    async def get_guids_by_ids(self, file_ids: Collection[int]) -> dict[int, str]:
        raise NotImplementedError

    async def delete_game_file_links(self, ids: Collection[int]) -> None:
        raise NotImplementedError

    async def get_unlinked_file_metas(
        self, ignored_game_link_ids: Collection[int] = ()
    ) -> list[hints.VerifiableFileMeta]:
        """Files with no ``level_files`` and no ``game_files`` row.

        ``ignored_game_link_ids`` are ``game_files`` rows to read as if they were
        already gone, so a dry run can tell what deleting them would orphan.
        """
        raise NotImplementedError

    async def delete_file_metas(self, guids: Collection[str]) -> None:
        raise NotImplementedError

    async def get_paths_by_guid(self) -> dict[str, str]:
        """Where every known file's content is, by guid.

        Several metas may share one path, so the content of a deleted meta may
        only be removed once no other guid maps to it.
        """
        raise NotImplementedError
