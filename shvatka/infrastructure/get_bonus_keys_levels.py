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
from shvatka.tgbot.main_factory import get_bot_specific_providers


async def main():
    paths = common_get_paths("CRAWLER_PATH")

    setup_logging(paths)
    dishka = make_async_container(
        *get_providers("CRAWLER_PATH"),
        *get_bot_specific_providers(),
    )
    try:
        async with dishka() as rd:
            dao = await rd.get(HolderDao)
            levels = sorted([l.scenario for l in await dao.level._get_all() if l.scenario.get_bonus_keys()], key=lambda l: l.id)
            for level in levels:
                print(level.id)
                bonuses = sorted(level.get_bonus_keys(), key=lambda b: b.text)
                for bk in bonuses:
                    print(bk.text, bk.bonus_minutes)
                print()

    finally:
        await dishka.close()


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
