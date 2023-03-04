from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.infrastructure.db.config.models.db import RedisConfig
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.scheduler import ApScheduler


def create_scheduler(
    pool: async_sessionmaker[AsyncSession],
    redis: Redis,
    bot: Bot,
    redis_config: RedisConfig,
    game_log_chat: int,
    file_storage: FileStorage,
    level_test_dao: LevelTestingData,
) -> Scheduler:
    return ApScheduler(
        redis_config=redis_config,
        pool=pool,
        redis=redis,
        bot=bot,
        game_log_chat=game_log_chat,
        file_storage=file_storage,
        level_test_dao=level_test_dao,
    )
