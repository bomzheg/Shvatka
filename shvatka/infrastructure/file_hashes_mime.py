"""
Migration script: backfill sha256, mime_type and extension for existing files.

For every file_info row missing them, the physical file is read to compute its
sha256 and detect its mime_type; a missing extension is then derived from the
mime_type (renaming the physical file accordingly and keeping file_path in
sync).  A final pass repairs any file_path left without its extension by an
earlier run.  No file_info rows are deleted and no scenario JSONs are touched.

Safe to re-run; every step is idempotent.

Run with:
    python -m shvatka.infrastructure.file_hashes_mime
"""

import asyncio
import logging
from pathlib import Path

from dishka import make_async_container
from sqlalchemy import select, ScalarResult
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
from shvatka.infrastructure.di import get_providers
from shvatka.infrastructure.di.infra import get_infra_only_providers

logger = logging.getLogger(__name__)


async def fill_hashes(
    session: AsyncSession,
    file_storage: FileStorage,
    batch_size: int = 100,
) -> None:
    """Compute and store sha256 + mime_type for all files that are missing them."""
    offset = 0
    while True:
        result: ScalarResult[models.FileInfo] = await session.scalars(
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
                with await file_storage.get(link) as content:
                    data = content.read()
            except (IOError, OSError) as e:
                logger.error("cannot read %s: %s", db_file.file_path, e)
                continue

            sha256 = compute_sha256(data)
            mime_type = detect_mime_type(data)

            db_file.sha256 = sha256
            db_file.mime_type = mime_type
            logger.info(
                "detected sha for %s (mime: %s)",
                db_file.guid,
                mime_type,
            )

        await session.commit()
        logger.info("processed batch at offset %d", offset)
        offset += batch_size


async def fill_extension(
    session: AsyncSession,
    batch_size: int = 100,
) -> None:
    """Backfill a missing extension and rename the physical file to match.

    For files whose extension is empty, derive it from the detected mime type,
    rename the physical file to include it and keep file_path in sync with the
    new on-disk name (file_path is authoritative for serving).
    """
    offset = 0
    while True:
        result: ScalarResult[models.FileInfo] = await session.scalars(
            select(models.FileInfo)
            .where(models.FileInfo.extension == "")
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

            mime_type = db_file.mime_type
            extension = db_file.extension or extension_from_mime(mime_type)

            db_file.mime_type = mime_type
            if not db_file.extension and extension:
                if db_file.extension != extension:
                    old_path = Path(db_file.file_path)
                    new_path = db_file.file_path + extension
                    old_path.rename(new_path)
                    db_file.extension = extension
                    db_file.file_path = new_path
                    logger.info(
                        "detected extension %s for %s (mime: %s)",
                        extension,
                        db_file.guid,
                        mime_type,
                    )

        await session.commit()
        logger.info("processed batch at offset %d", offset)
        offset += batch_size


async def repair_file_path_extensions(
    session: AsyncSession,
    batch_size: int = 100,
) -> None:
    """Repair file_path values that are missing their extension.

    An earlier fill_extension run renamed the physical file to include the
    extension but did not update file_path. Since serving now resolves the
    physical file by file_path, bring file_path back in sync with the on-disk
    name (file_path + extension) for any such row. Idempotent.
    """
    offset = 0
    repaired = 0
    while True:
        result: ScalarResult[models.FileInfo] = await session.scalars(
            select(models.FileInfo)
            .where(models.FileInfo.extension != "")
            .where(models.FileInfo.file_path.is_not(None))
            .order_by(models.FileInfo.id)
            .limit(batch_size)
            .offset(offset)
        )
        batch = list(result.all())
        if not batch:
            break

        for db_file in batch:
            if not db_file.file_path.endswith(db_file.extension):
                db_file.file_path = db_file.file_path + db_file.extension
                repaired += 1
                logger.info(
                    "repaired file_path for %s -> %s", db_file.guid, db_file.file_path
                )

        await session.commit()
        offset += batch_size
    logger.info("repaired %d file_path values", repaired)


async def main() -> None:
    paths = common_get_paths("INFRA_PATH")
    setup_logging(paths)
    dishka = make_async_container(
        *get_providers("INFRA_PATH"),
        *get_infra_only_providers(),
    )
    try:
        async with dishka() as request_dishka:
            file_storage = await request_dishka.get(FileStorage)
            session = await request_dishka.get(AsyncSession)
            await fill_hashes(session, file_storage)
            await fill_extension(session)
            await repair_file_path_extensions(session)
    finally:
        await dishka.close()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
