import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog import DialogRegistry
from dataclass_factory import Factory
from redis.asyncio.client import Redis
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from db.locker import MemoryLockFactory
from scheduler import ApScheduler
from shvatka.models.config import Config
from shvatka.models.config.db import RedisConfig, DBConfig
from shvatka.models.config.main import Paths
from shvatka.models.config.storage import StorageConfig, StorageType
from shvatka.scheduler import Scheduler
from shvatka.services.username_resolver.user_getter import UserGetter
from shvatka.utils.key_checker_lock import KeyCheckerFactory
from tgbot.dialogs import setup_dialogs
from tgbot.handlers import setup_handlers
from tgbot.middlewares import setup_middlewares

logger = logging.getLogger(__name__)


def create_bot(config: Config) -> Bot:
    return Bot(
        token=config.bot.token,
        parse_mode="HTML",
        session=config.bot.create_session(),
    )


def create_dispatcher(
    config: Config, user_getter: UserGetter, dcf: Factory, pool: sessionmaker,
    redis: Redis, scheduler: Scheduler, locker: KeyCheckerFactory,
) -> Dispatcher:
    dp = Dispatcher(storage=create_storage(config.storage))
    setup_middlewares(
        dp=dp,
        pool=pool,
        bot_config=config.bot,
        user_getter=user_getter,
        dcf=dcf,
        redis=redis,
        scheduler=scheduler,
        locker=locker,
    )
    registry = DialogRegistry(dp)
    setup_dialogs(registry)
    setup_handlers(dp, config.bot)
    return dp


def create_storage(config: StorageConfig) -> BaseStorage:
    logger.info("creating storage for type %s", config.type_)
    match config.type_:
        case StorageType.memory:
            return MemoryStorage()
        case StorageType.redis:
            return RedisStorage(create_redis(config.redis))
        case _:
            raise NotImplementedError


def create_scheduler(
    pool: sessionmaker, redis: Redis, bot: Bot, redis_config: RedisConfig, game_log_chat: int,
) -> Scheduler:
    return ApScheduler(
        redis_config=redis_config, pool=pool, redis=redis,
        bot=bot, game_log_chat=game_log_chat,
    )


def get_paths() -> Paths:
    if path := os.getenv("BOT_PATH"):
        return Paths(Path(path))
    return Paths(Path(__file__).parent.parent)


def create_pool(db_config: DBConfig) -> sessionmaker:
    engine = create_async_engine(url=make_url(db_config.uri), echo=True)
    pool = sessionmaker(bind=engine, class_=AsyncSession,
                        expire_on_commit=False, autoflush=False)
    return pool


def create_lock_factory() -> KeyCheckerFactory:
    return MemoryLockFactory()


def create_redis(config: RedisConfig) -> Redis:
    logger.info("created redis for %s", config)
    return Redis(host=config.url, port=config.port, db=config.db)
