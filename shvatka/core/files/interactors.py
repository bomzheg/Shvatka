import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from shvatka.core.files.adapters import FileGarbageCollectorDao
from shvatka.core.files.dto import FileGarbage, GameFileLink
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models.dto import hints
from shvatka.core.utils.datetime_utils import tz_utc

logger = logging.getLogger(__name__)

STORAGE_ORPHAN_MIN_AGE = timedelta(days=1)
"""How long a stored file has to look unreferenced before it may be swept.

Content reaches the storage before its ``files_info`` row is committed, so an
upload running right now looks exactly like a leftover. Age is what tells them
apart — anything younger is left for the next run.
"""


@dataclass
class CollectFileGarbageInteractor:
    dao: FileGarbageCollectorDao
    storage: FileStorage

    async def __call__(self, identity: IdentityProvider, dry_run: bool = False) -> FileGarbage:
        admin = await identity.get_superuser()
        release_guids = await self.dao.get_release_guids()

        garbage_links = await self._find_unused_links(release_guids)
        link_ids = [link.id for link in garbage_links]
        if link_ids and not dry_run:
            await self.dao.delete_game_file_links(link_ids)

        released = {guid for guids in release_guids.values() for guid in guids}
        # if links are deleted - pass link_ids is redundant.
        # but for dry run passing links can emulate that links was deleted
        orphans = [
            meta
            for meta in await self.dao.get_unlinked_file_metas(ignored_game_link_ids=link_ids)
            if meta.guid not in released
        ]
        orphan_guids = [meta.guid for meta in orphans]
        if orphan_guids and not dry_run:
            await self.dao.delete_file_metas(orphan_guids)

        # TODO probably OOM. should replace to some SQL and work by chunks.
        paths_by_guid = await self.dao.get_paths_by_guid()
        for guid in orphan_guids:
            paths_by_guid.pop(guid, None)
        stored_garbage = await self._find_stored_garbage(alive_paths=set(paths_by_guid.values()))

        if not dry_run:
            # the db first: a file left on the storage is swept by the next run,
            # while a meta pointing at content that is gone is a broken download
            await self.dao.commit()
            for link in stored_garbage:
                await self.storage.delete(link)

        garbage = FileGarbage(
            game_links=garbage_links,
            file_guids=orphan_guids,
            stored_files=[link.file_path for link in stored_garbage],
            dry_run=dry_run,
        )
        logger.warning(
            "admin %s collected file garbage (dry_run=%s): "
            "%s game links, %s file metas, %s stored files",
            admin.id,
            dry_run,
            len(garbage.game_links),
            len(garbage.file_guids),
            len(garbage.stored_files),
        )
        return garbage

    async def _find_unused_links(self, release_guids: dict[int, set[str]]) -> list[GameFileLink]:
        links = await self.dao.get_unused_game_file_links()
        if not links:
            return []
        guids = await self.dao.get_guids_by_ids({link.file_id for link in links})
        return [
            link
            for link in links
            if guids.get(link.file_id) not in release_guids.get(link.game_id, frozenset())
        ]

    async def _find_stored_garbage(self, alive_paths: set[str]) -> list[hints.FileContentLink]:
        oldest_to_keep = datetime.now(tz=tz_utc) - STORAGE_ORPHAN_MIN_AGE
        return [
            file.link
            for file in await self.storage.list_files()
            if file.link.file_path not in alive_paths and file.modified_at < oldest_to_keep
        ]
