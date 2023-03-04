from dataclasses import dataclass

from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.core.interfaces.clients.file_storage import FileStorage
from src.core.interfaces.scheduler import Scheduler
from src.infrastructure.db.dao.holder import HolderDao
from src.infrastructure.db.dao.memory.level_testing import LevelTestingData


class ScheduledContextHolder:
    """
    ATTENTION!
    GLOBAL VARIABLE!
    """

    pool: async_sessionmaker[AsyncSession]
    redis: Redis
    bot: Bot
    scheduler: Scheduler
    file_storage: FileStorage
    game_log_chat: int
    level_test_dao: LevelTestingData


@dataclass
class ScheduledContext:
    dao: HolderDao  # need wrappers or protocols
    bot: Bot  # need wrappers or protocols
    file_storage: FileStorage
    scheduler: Scheduler
    game_log_chat: int
