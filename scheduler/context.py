from dataclasses import dataclass

from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.orm import sessionmaker

from db.dao.holder import HolderDao
from db.dao.memory.level_testing import LevelTestingData
from shvatka.clients.file_storage import FileStorage
from shvatka.scheduler import Scheduler


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
