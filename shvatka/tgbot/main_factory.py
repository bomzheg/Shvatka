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

from shvatka.common import create_dataclass_factory, create_telegraph
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.db.config.models.storage import StorageConfig, StorageType
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.db.factory import (
    create_redis,
    create_level_test_dao,
    create_lock_factory,
)
from shvatka.infrastructure.scheduler.factory import create_scheduler
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.handlers import setup_handlers
from shvatka.tgbot.middlewares import setup_middlewares
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.utils.router import print_router_tree
from shvatka.tgbot.views.jinja_filters import setup_jinja
from shvatka.tgbot.views.telegraph import Telegraph

logger = logging.getLogger(__name__)


class DpBuilder:
    def __init__(
        self,
        config: TgBotConfig,
        pool: async_sessionmaker[AsyncSession],
        file_storage: FileStorage,
    ):
        self.config = config
        self.pool = pool
        self.file_storage = file_storage
        self.dcf = create_dataclass_factory()
        self.bot = create_bot(config)
        self.level_test_dao = create_level_test_dao()
        self.user_getter = UserGetter(self.config.tg_client)
        self.redis = create_redis(self.config.redis)
        self.scheduler = create_scheduler(
            pool=self.pool,
            redis=self.redis,
            bot=self.bot,
            redis_config=self.config.redis,
            game_log_chat=self.config.bot.log_chat,
            file_storage=self.file_storage,
            level_test_dao=self.level_test_dao,
        )
        self.dp = create_dispatcher(
            config=self.config,
            user_getter=self.user_getter,
            dcf=self.dcf,
            pool=self.pool,
            redis=self.redis,
            scheduler=self.scheduler,
            locker=create_lock_factory(),
            file_storage=self.file_storage,
            level_test_dao=self.level_test_dao,
            telegraph=create_telegraph(self.config.bot),
            message_manager=MessageManager(),
        )
        self.initialized = False

    async def start(self) -> tuple[Bot, Dispatcher]:
        if not self.initialized:
            setup_jinja(bot=self.bot)
            await self.user_getter.start()
            await self.redis.initialize()
            await self.scheduler.start()
        return self.bot, self.dp

    async def close(self) -> None:
        await self.scheduler.close()
        await self.redis.close()
        await self.user_getter.stop()

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.close()


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
        config=config,
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
    logger.info("Configured bot routers \n%s", print_router_tree(dp))
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


def resolve_update_types(dp: Dispatcher) -> list[str]:
    return dp.resolve_used_update_types(skip_events={"aiogd_update"})
