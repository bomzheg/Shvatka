from dataclasses import dataclass

from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.orm import sessionmaker

from db.dao.holder import HolderDao
from scheduler import ApScheduler
from shvatka.clients.file_storage import FileStorage


class ScheduledContextHolder:
    """
    ATTENTION!
    GLOBAL VARIABLE!
    """
    poll: sessionmaker
    redis: Redis
    bot: Bot
    scheduler: ApScheduler
    file_storage: FileStorage
    game_log_chat: int


@dataclass
class ScheduledContext:
    dao: HolderDao  # need wrappers or protocols
    bot: Bot  # need wrappers or protocols
    file_storage: FileStorage
    scheduler: ApScheduler
    game_log_chat: int
