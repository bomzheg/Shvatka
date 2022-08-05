import asyncio
import logging

import dataclass_factory
from sqlalchemy.orm import close_all_sessions

from app.config import load_config
from app.config.logging_config import setup_logging
from app.main_factory import create_bot, create_dispatcher, get_paths
from app.services.username_resolver.user_getter import UserGetter

logger = logging.getLogger(__name__)


async def main():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    dcf = dataclass_factory.Factory()

    async with UserGetter(config.tg_client) as user_getter:
        dp = create_dispatcher(config, user_getter, dcf)
        bot = create_bot(config)

        logger.info("started")
        try:
            await dp.start_polling(bot)
        finally:
            close_all_sessions()
            await bot.session.close()
            logger.info("stopped")


if __name__ == '__main__':
    asyncio.run(main())
