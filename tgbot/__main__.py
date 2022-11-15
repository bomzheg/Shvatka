import asyncio
import logging

import dataclass_factory
from dataclass_factory import Schema, NameStyle
from sqlalchemy.orm import close_all_sessions

from common.config.parser.logging_config import setup_logging
from db.dao.memory.level_testing import LevelTestingData
from db.fatory import create_pool, create_lock_factory
from shvatka.models.schems import schemas
from tgbot.config.parser.main import load_config
from tgbot.main_factory import (
    create_bot,
    create_dispatcher,
    get_paths,
    create_scheduler,
    create_redis, create_file_storage,
)
from tgbot.username_resolver.user_getter import UserGetter

logger = logging.getLogger(__name__)


async def main():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    dcf = dataclass_factory.Factory(schemas=schemas, default_schema=Schema(name_style=NameStyle.kebab))
    file_storage = create_file_storage(config.file_storage_config)
    pool = create_pool(config.db)
    bot = create_bot(config)
    level_test_dao = LevelTestingData()

    async with (
        UserGetter(config.tg_client) as user_getter,
        create_redis(config.redis) as redis,
        create_scheduler(
            pool=pool, redis=redis, bot=bot, redis_config=config.redis,
            game_log_chat=config.bot.log_chat, file_storage=file_storage,
            level_test_dao=level_test_dao
        ) as scheduler,
    ):
        dp = create_dispatcher(
            config=config, user_getter=user_getter, dcf=dcf, pool=pool,
            redis=redis, scheduler=scheduler, locker=create_lock_factory(),
            file_storage=file_storage, level_test_dao=level_test_dao,
        )

        logger.info("started")
        try:
            await dp.start_polling(bot)
        finally:
            close_all_sessions()
            await bot.session.close()
            await redis.close()
            logger.info("stopped")


if __name__ == '__main__':
    asyncio.run(main())
