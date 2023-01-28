from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.orm import sessionmaker

from infrastructure.db.config.models.db import RedisConfig
from infrastructure.db.dao.memory.level_testing import LevelTestingData
from infrastructure.scheduler import ApScheduler
from shvatka.interfaces.clients.file_storage import FileStorage
from shvatka.interfaces.scheduler import Scheduler


def create_scheduler(
    pool: sessionmaker,
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
