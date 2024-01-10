from aiogram import Dispatcher
from aiogram_dialog.api.protocols import BgManagerFactory
from dataclass_factory import Factory
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.views.telegraph import Telegraph
from .config_middleware import ConfigMiddleware
from .data_load_middleware import LoadDataMiddleware
from .fix_target_middleware import FixTargetMiddleware
from .init_middleware import InitMiddleware
from .load_team_player import TeamPlayerMiddleware
from ..config.models.main import TgBotConfig


def setup_middlewares(
    dp: Dispatcher,
    pool: async_sessionmaker[AsyncSession],
    config: TgBotConfig,
    user_getter: UserGetter,
    dcf: Factory,
    redis: Redis,
    scheduler: Scheduler,
    locker: KeyCheckerFactory,
    file_storage: FileStorage,
    level_test_dao: LevelTestingData,
    telegraph: Telegraph,
    bg_manager_factory: BgManagerFactory,
):
    dp.update.middleware(ConfigMiddleware(config.bot, config))
    dp.update.middleware(
        InitMiddleware(
            pool=pool,
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
    )
    dp.update.middleware(LoadDataMiddleware())
    dp.message.middleware(FixTargetMiddleware())
