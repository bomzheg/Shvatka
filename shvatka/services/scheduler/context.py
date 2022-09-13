from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.orm import sessionmaker


class ScheduledContextHolder:
    """
    ATTENTION!
    GLOBAL VARIABLE!
    """
    poll: sessionmaker
    redis: Redis
    bot: Bot
