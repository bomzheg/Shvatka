"""
Migration script: compute sha256 and mime_type for all existing files,
then deduplicate: for each group of files sharing the same sha256, keep
the record with the lowest id (oldest) and rewrite every Level scenario
that references a duplicate guid to point to the canonical guid instead.
Duplicate files_info records and their physical files are removed.

Run with:
    python -m shvatka.infrastructure.file_deduplicator
"""

import asyncio
import logging
from collections import defaultdict
from pathlib import Path

from dishka import make_async_container
from sqlalchemy import select, delete
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
    """Find files sharing the same sha256 and collapse duplicates.

    For each duplicate group:
    - Keep the record with the lowest id (canonical).
    - Update every Level scenario that references a duplicate guid to use the
      canonical guid instead.
    - Delete duplicate files_info records and their physical files.
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

    replacement: dict[str, str] = {}
    dup_paths: list[str] = []
    for sha256, files in duplicate_groups.items():
        canonical = files[0]
        for dup in files[1:]:
            replacement[dup.guid] = canonical.guid
            if dup.file_path:
                dup_paths.append(dup.file_path)
            logger.info(
                "duplicate guid=%s -> canonical guid=%s (sha256=%.12s...)",
                dup.guid,
                canonical.guid,
                sha256,
            )

    if replacement:
        await _rewrite_scenarios(session, replacement)
        await _delete_duplicates(session, list(replacement.keys()), dup_paths)
        await session.commit()

    logger.info("deduplication complete, removed %d duplicate records", len(replacement))


async def _rewrite_scenarios(session: AsyncSession, replacement: dict[str, str]) -> None:
    """Load all Level scenarios and replace duplicate guids with canonical guids."""
    result = await session.scalars(select(models.Level))
    levels = list(result.all())

    for level in levels:
        if level.scenario is None:
            continue
        scenario_dict = _scenario_to_dict(level.scenario)
        changed, new_dict = _replace_guids_in_dict(scenario_dict, replacement)
        if changed:
            assert isinstance(new_dict, dict)
            level.scenario = _dict_to_scenario(new_dict)
            logger.info("updated scenario for level id=%d name=%s", level.id, level.name_id)


def _scenario_to_dict(scenario) -> dict:
    from shvatka.infrastructure.db.models.level import ScenarioField
    from shvatka.core.models.dto import scn

    return ScenarioField.retort.dump(scenario, scn.LevelScenario)


def _dict_to_scenario(d: dict):
    from shvatka.infrastructure.db.models.level import ScenarioField
    from shvatka.core.models.dto import scn

    return ScenarioField.retort.load(d, scn.LevelScenario)


def _replace_guids_in_dict(obj, replacement: dict[str, str]) -> tuple[bool, object]:
    """Recursively walk a JSON-like structure and replace guid values."""
    changed = False
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            sub_changed, new_v = _replace_guids_in_dict(v, replacement)
            if sub_changed:
                changed = True
            new_obj[k] = new_v
        return changed, new_obj
    elif isinstance(obj, list):
        new_list = []
        for item in obj:
            sub_changed, new_item = _replace_guids_in_dict(item, replacement)
            if sub_changed:
                changed = True
            new_list.append(new_item)
        return changed, new_list
    elif isinstance(obj, str) and obj in replacement:
        return True, replacement[obj]
    return False, obj


async def _delete_duplicates(
    session: AsyncSession,
    dup_guids: list[str],
    dup_paths: list[str],
) -> None:
    for path_str in dup_paths:
        path = Path(path_str)
        if path.exists():
            try:
                path.unlink()
                logger.info("deleted physical file %s", path)
            except OSError as e:
                logger.error("could not delete %s: %s", path, e)

    await session.execute(delete(models.FileInfo).where(models.FileInfo.guid.in_(dup_guids)))


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

        logger.info("=== Step 2: deduplicating ===")
        await deduplicate(session)
    finally:
        await dishka.close()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
