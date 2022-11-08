import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from dataclass_factory import Factory
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from clients.file_storage import LocalFileStorage
from common.config.models.main import FileStorageConfig
from common.config.models.paths import Paths
from common.config.parser.paths import common_get_paths
from db.config.models.db import RedisConfig
from db.config.models.storage import StorageConfig, StorageType
from db.fatory import create_redis
from scheduler import ApScheduler
from shvatka.clients.file_storage import FileStorage
from shvatka.scheduler import Scheduler
from shvatka.utils.key_checker_lock import KeyCheckerFactory
from tgbot.config.models.main import TgBotConfig
from tgbot.handlers import setup_handlers
from tgbot.middlewares import setup_middlewares
from tgbot.username_resolver.user_getter import UserGetter

logger = logging.getLogger(__name__)


def create_bot(config: TgBotConfig) -> Bot:
    return Bot(
        token=config.bot.token,
        parse_mode="HTML",
        session=config.bot.create_session(),
    )


def create_dispatcher(
    config: TgBotConfig, user_getter: UserGetter, dcf: Factory, pool: sessionmaker,
    redis: Redis, scheduler: Scheduler, locker: KeyCheckerFactory, file_storage: FileStorage,
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
        file_storage=file_storage,
    )
    setup_handlers(dp, config.bot)
    return dp


def create_storage(config: StorageConfig) -> BaseStorage:
    logger.info("creating storage for type %s", config.type_)
    match config.type_:
        case StorageType.memory:
            return MemoryStorage()
        case StorageType.redis:
            return RedisStorage(create_redis(config.redis), key_builder=DefaultKeyBuilder(with_destiny=True))
        case _:
            raise NotImplementedError


def create_file_storage(config: FileStorageConfig) -> FileStorage:
    return LocalFileStorage(config)


def create_scheduler(
    pool: sessionmaker, redis: Redis, bot: Bot, redis_config: RedisConfig,
    game_log_chat: int, file_storage: FileStorage,
) -> Scheduler:
    return ApScheduler(
        redis_config=redis_config, pool=pool, redis=redis,
        bot=bot, game_log_chat=game_log_chat, file_storage=file_storage
    )


def get_paths() -> Paths:
    return common_get_paths("BOT_PATH")
