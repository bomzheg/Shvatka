"""
Migration script: compute sha256 and mime_type for all existing files, then
deduplicate physical storage by pointing every duplicate file_info row at the
canonical (oldest) physical file.

No file_info rows are deleted and no scenario JSONs are touched.  The result is
that multiple file_info records (each with their own guid) share a single file
on disk.  Orphaned physical files whose path is no longer referenced are removed.

Run with:
    python -m shvatka.infrastructure.file_deduplicator
"""

import asyncio
import logging
from collections import defaultdict
from pathlib import Path

from dishka import make_async_container
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.common import setup_logging
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models.dto import hints
from shvatka.infrastructure.clients.file_storage import (
    compute_sha256,
    detect_mime_type,
    extension_from_mime,
)
from shvatka.infrastructure.db import models
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.di import get_providers

logger = logging.getLogger(__name__)


async def fill_hashes_and_mime(
    session: AsyncSession,
    file_storage: FileStorage,
    batch_size: int = 100,
) -> None:
    """Compute and store sha256 + mime_type for all files that are missing them."""
    offset = 0
    while True:
        result = await session.scalars(
            select(models.FileInfo)
            .where(models.FileInfo.sha256.is_(None))
            .order_by(models.FileInfo.id)
            .limit(batch_size)
            .offset(offset)
        )
        batch = list(result.all())
        if not batch:
            break

        for db_file in batch:
            if not db_file.file_path:
                logger.warning("file %s has no file_path, skipping", db_file.guid)
                continue
            link = hints.FileContentLink(file_path=db_file.file_path)
            try:
                content = await file_storage.get(link)
                data = content.read()
            except (IOError, OSError) as e:
                logger.error("cannot read %s: %s", db_file.file_path, e)
                continue

            sha256 = compute_sha256(data)
            mime_type = detect_mime_type(data)
            extension = db_file.extension or extension_from_mime(mime_type)

            db_file.sha256 = sha256
            db_file.mime_type = mime_type
            if not db_file.extension and extension:
                db_file.extension = extension
                logger.info(
                    "detected extension %s for %s (mime: %s)", extension, db_file.guid, mime_type
                )

        await session.commit()
        logger.info("processed batch at offset %d", offset)
        offset += batch_size


async def deduplicate(session: AsyncSession) -> None:
    """Point every duplicate file_info row at the canonical physical file.

    For each group of rows sharing the same sha256:
    - The row with the lowest id is the canonical one (its file_path is kept).
    - All other rows have their file_path updated to the canonical path.
    - The now-orphaned physical files are deleted from disk.

    No file_info rows are removed and no scenario JSONs are modified.
    """
    result = await session.scalars(
        select(models.FileInfo)
        .where(models.FileInfo.sha256.is_not(None))
        .order_by(models.FileInfo.sha256, models.FileInfo.id)
    )
    all_files = list(result.all())

    groups: dict[str, list[models.FileInfo]] = defaultdict(list)
    for f in all_files:
        groups[f.sha256].append(f)

    duplicate_groups = {h: files for h, files in groups.items() if len(files) > 1}
    if not duplicate_groups:
        logger.info("no duplicates found")
        return

    logger.info("found %d duplicate groups", len(duplicate_groups))

    redirected = 0
    for sha256, files in duplicate_groups.items():
        canonical = files[0]
        canonical_path = canonical.file_path
        if not canonical_path:
            logger.warning("canonical record %s has no file_path, skipping group", canonical.guid)
            continue

        for dup in files[1:]:
            orphan_path = dup.file_path
            if orphan_path and orphan_path != canonical_path:
                _delete_physical_file(orphan_path)

            await session.execute(
                update(models.FileInfo)
                .where(models.FileInfo.guid == dup.guid)
                .values(file_path=canonical_path)
            )
            logger.info(
                "redirected guid=%s -> canonical path=%s (sha256=%.12s...)",
                dup.guid,
                canonical_path,
                sha256,
            )
            redirected += 1

    await session.commit()
    logger.info("deduplication complete, redirected %d duplicate records", redirected)


def _delete_physical_file(path_str: str) -> None:
    path = Path(path_str)
    if path.exists():
        try:
            path.unlink()
            logger.info("deleted orphaned physical file %s", path)
        except OSError as e:
            logger.error("could not delete %s: %s", path, e)


async def main() -> None:
    paths = common_get_paths("CRAWLER_PATH")
    setup_logging(paths)
    dishka = make_async_container(*get_providers("CRAWLER_PATH"))
    try:
        holder = await dishka.get(HolderDao)
        file_storage = await dishka.get(FileStorage)
        session: AsyncSession = holder.file_info.session

        logger.info("=== Step 1: filling sha256 and mime_type ===")
        await fill_hashes_and_mime(session, file_storage)

        logger.info("=== Step 2: deduplicating physical files ===")
        await deduplicate(session)
    finally:
        await dishka.close()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
