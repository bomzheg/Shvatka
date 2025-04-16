import asyncio
import logging

from aiogram import Dispatcher, Bot

from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.infrastructure.di.utils import warm_up

from shvatka.tgbot.main_factory import (
    resolve_update_types,
    create_dishka,
)

logger = logging.getLogger(__name__)


async def main():
    paths = common_get_paths("BOT_PATH")
    setup_logging(paths)
    dishka = create_dishka("BOT_PATH")
    dp = await dishka.get(Dispatcher)
    bot = await dishka.get(Bot)

    try:
        await warm_up(dishka)
        await bot.delete_webhook()
        await dp.start_polling(bot, allowed_updates=resolve_update_types(dp))
    finally:
        logger.info("stopped")
        await dishka.close()


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
