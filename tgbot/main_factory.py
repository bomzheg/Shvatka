import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram_dialog import DialogRegistry
from dataclass_factory import Factory
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from app.models.config import Config
from app.models.config.db import RedisConfig
from app.models.config.main import Paths
from app.services.scheduler.scheduler import Scheduler
from app.services.username_resolver.user_getter import UserGetter
from tgbot.handlers import setup_handlers
from tgbot.handlers.dialogs import setup_dialogs
from tgbot.middlewares import setup_middlewares


def create_bot(config: Config) -> Bot:
    return Bot(
        token=config.bot.token,
        parse_mode="HTML",
        session=config.bot.create_session(),
    )


def create_dispatcher(
    config: Config, user_getter: UserGetter, dcf: Factory, pool: sessionmaker,
    redis: Redis, scheduler: Scheduler,
) -> Dispatcher:
    dp = Dispatcher(storage=(config.storage.create_storage()))
    setup_middlewares(
        dp=dp,
        pool=pool,
        bot_config=config.bot,
        user_getter=user_getter,
        dcf=dcf,
        redis=redis,
        scheduler=scheduler,
    )
    registry = DialogRegistry(dp)
    setup_dialogs(registry)
    setup_handlers(dp, config.bot)
    return dp


def create_scheduler(
    pool: sessionmaker, redis: Redis, bot: Bot, redis_config: RedisConfig
) -> Scheduler:
    return Scheduler(redis_config=redis_config, pool=pool, redis=redis, bot=bot)


def get_paths() -> Paths:
    if path := os.getenv("BOT_PATH"):
        return Paths(Path(path))
    return Paths(Path(__file__).parent.parent)
