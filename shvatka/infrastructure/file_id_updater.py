import asyncio
import typing

from dishka import make_async_container

from shvatka.common import setup_logging
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.di import get_providers


async def main():
    paths = common_get_paths("CRAWLER_PATH")

    setup_logging(paths)
    dishka = make_async_container(
        *get_providers("CRAWLER_PATH"),
    )
    try:
        dao = await dishka.get(HolderDao)
        file_gateway = await dishka.get(FileGateway)
        await fill_all_file_id(dao.file_info, typing.cast(BotFileGateway, file_gateway))
    finally:
        await dishka.close()


async def fill_all_file_id(dao: FileInfoDao, file_gateway: BotFileGateway):
    while batch := await dao.get_without_file_id(100):
        for file in batch:
            await file_gateway.renew_file_id(file.author, file)
        await dao.commit()


if __name__ == "__main__":
    asyncio.run(main())
