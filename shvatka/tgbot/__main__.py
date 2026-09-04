import asyncio
import logging
import time

from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.common.config.parser.paths import common_get_paths

logger = logging.getLogger(__name__)


async def main():
    paths = common_get_paths("BOT_PATH")
    setup_logging(paths)
    logger.info("logging configured, loading application modules...")
    started_at = time.monotonic()
    from aiogram import Bot, Dispatcher

    from shvatka.infrastructure.di.utils import warm_up
    from shvatka.tgbot.main_factory import create_dishka, resolve_update_types

    logger.info("application modules loaded in %.2f s", time.monotonic() - started_at)

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
