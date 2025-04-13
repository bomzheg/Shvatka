import asyncio
import logging
import typing

from dishka import make_async_container

from shvatka.common import setup_logging
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.di import get_providers

logger = logging.getLogger(__name__)


async def main():
    paths = common_get_paths("CRAWLER_PATH")

    setup_logging(paths)
    dishka = make_async_container(
        *get_providers("CRAWLER_PATH"),
    )
    try:
        async with dishka() as request_dishka:
            dao: HolderDao = await request_dishka.get(HolderDao)
            games = await dao.game.get_completed_games()
            failed = []
            for game in games:
                logger.info("checking game #%s %s (%s)", game.id, game.name, game.number)
                try:
                    full = await dao.game.get_full(game.id)
                except Exception as e:
                    logger.exception("got error %s", game.id)
                    failed.append(game)
                    continue
                logger.debug("game %s, levels %s", full, full.levels)
            logger.info("errors %s", [(g.id, g.name) for g in failed])
    finally:
        await dishka.close()


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
