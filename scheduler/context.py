from dataclasses import dataclass

from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.orm import sessionmaker

from db.dao.holder import HolderDao
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
    game_log_chat: int


@dataclass
class ScheduledContext:
    dao: HolderDao  # need wrappers or protocols
    bot: Bot  # need wrappers or protocols
    scheduler: Scheduler
    game_log_chat: int
