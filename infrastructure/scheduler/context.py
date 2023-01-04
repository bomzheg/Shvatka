from dataclasses import dataclass

from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.orm import sessionmaker

from infrastructure.db.dao.holder import HolderDao
from infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.interfaces.clients.file_storage import FileStorage
from shvatka.interfaces.scheduler import Scheduler


class ScheduledContextHolder:
    """
    ATTENTION!
    GLOBAL VARIABLE!
    """

    poll: sessionmaker
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
