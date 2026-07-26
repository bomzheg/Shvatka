import asyncio
import logging
import typing
from io import BytesIO

from dishka import make_async_container

from shvatka.common import setup_logging
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.core.interfaces.clients.file_storage import FileGateway, FileStorage
from shvatka.core.models.dto import hints
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.clients.file_storage import (
    EMPTY_CONTENT_SHA256,
    compute_sha256,
    detect_mime_type,
)
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.di import get_providers
from shvatka.infrastructure.di.infra import get_infra_only_providers

logger = logging.getLogger(__name__)


async def main():
    paths = common_get_paths("INFRA_PATH")

    setup_logging(paths)
    dishka = make_async_container(
        *get_providers("INFRA_PATH"),
        *get_infra_only_providers(),
    )
    try:
        async with dishka() as request_dishka:
            dao = await request_dishka.get(HolderDao)
            storage = await request_dishka.get(FileStorage)
            file_gateway = await request_dishka.get(FileGateway)
            await repair_empty_files(
                dao.file_info, storage, typing.cast(BotFileGateway, file_gateway)
            )
    finally:
        await dishka.close()


async def repair_empty_files(
    dao: FileInfoDao, storage: FileStorage, file_gateway: BotFileGateway
) -> tuple[int, int]:
    """Restore files that were saved with no content, from their telegram copy.

    Uploading to telegram used to consume the content stream, so the storage
    wrote an empty file while the telegram upload itself succeeded. Those files
    are recognisable by the sha256 of empty content and still carry a usable
    file_id, so the content can be downloaded back.

    Returns how many files were repaired and how many were left alone.
    """
    broken = await dao.get_by_sha256(EMPTY_CONTENT_SHA256)
    logger.info("found %s empty files", len(broken))
    repaired = skipped = 0
    for file in broken:
        if await _repair_file(file, storage, file_gateway, dao):
            repaired += 1
        else:
            skipped += 1
    await dao.commit()
    logger.info("repaired %s files, left %s as is", repaired, skipped)
    return repaired, skipped


async def _repair_file(
    file: hints.VerifiableFileMeta,
    storage: FileStorage,
    file_gateway: BotFileGateway,
    dao: FileInfoDao,
) -> bool:
    if file.tg_link is None:
        logger.warning("file %s is empty and has no file_id, can't restore it", file.guid)
        return False
    try:
        content = await file_gateway.download_from_tg(file.tg_link)
    except Exception as e:
        logger.error("can't download file %s from telegram", file.guid, exc_info=e)
        return False
    data = content.read()
    if not data:
        logger.warning("telegram returned no content for file %s", file.guid)
        return False
    await storage.put_content(file.local_file_name, BytesIO(data))
    await dao.update_sha256_and_mime(file.guid, compute_sha256(data), detect_mime_type(data))
    logger.info("restored %s bytes of file %s", len(data), file.guid)
    return True


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
