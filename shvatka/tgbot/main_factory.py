import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder, RedisEventIsolation
from aiogram_dialog.manager.message_manager import MessageManager
from dataclass_factory import Factory
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.db.config.models.storage import StorageConfig, StorageType
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.db.factory import create_redis
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.handlers import setup_handlers
from shvatka.tgbot.middlewares import setup_middlewares
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.views.telegraph import Telegraph

logger = logging.getLogger(__name__)


def create_bot(config: TgBotConfig) -> Bot:
    return Bot(
        token=config.bot.token,
        parse_mode=ParseMode.HTML,
        session=config.bot.create_session(),
    )


def create_dispatcher(
    config: TgBotConfig,
    user_getter: UserGetter,
    dcf: Factory,
    pool: async_sessionmaker[AsyncSession],
    redis: Redis,
    scheduler: Scheduler,
    locker: KeyCheckerFactory,
    file_storage: FileStorage,
    level_test_dao: LevelTestingData,
    telegraph: Telegraph,
    message_manager: MessageManager,
) -> Dispatcher:
    dp = create_only_dispatcher(config, redis)
    bg_manager_factory = setup_handlers(dp, config.bot, message_manager)
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
        level_test_dao=level_test_dao,
        telegraph=telegraph,
        bg_manager_factory=bg_manager_factory,
    )
    return dp


def create_only_dispatcher(config, redis):
    dp = Dispatcher(
        storage=create_storage(config.storage),
        events_isolation=RedisEventIsolation(redis=redis),
    )
    return dp


def create_storage(config: StorageConfig) -> BaseStorage:
    logger.info("creating storage for type %s", config.type_)
    match config.type_:
        case StorageType.memory:
            return MemoryStorage()
        case StorageType.redis:
            if config.redis is None:
                raise ValueError("you have to specify redis config for use redis storage")
            return RedisStorage(
                create_redis(config.redis), key_builder=DefaultKeyBuilder(with_destiny=True)
            )
        case _:
            raise NotImplementedError


def get_paths() -> Paths:
    return common_get_paths("BOT_PATH")
