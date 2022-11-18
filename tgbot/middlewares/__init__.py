from aiogram import Dispatcher
from dataclass_factory import Factory
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from db.dao.memory.level_testing import LevelTestingData
from shvatka.clients.file_storage import FileStorage
from shvatka.scheduler import Scheduler
from shvatka.utils.key_checker_lock import KeyCheckerFactory
from tgbot.config.models.bot import BotConfig
from tgbot.middlewares.config_middleware import ConfigMiddleware
from tgbot.middlewares.data_load_middleware import LoadDataMiddleware
from tgbot.middlewares.fix_target_middleware import FixTargetMiddleware
from tgbot.middlewares.init_middleware import InitMiddleware
from tgbot.username_resolver.user_getter import UserGetter
from tgbot.views.telegraph import Telegraph


def setup_middlewares(
    dp: Dispatcher, pool: sessionmaker, bot_config: BotConfig,
    user_getter: UserGetter, dcf: Factory, redis: Redis, scheduler: Scheduler,
    locker: KeyCheckerFactory, file_storage: FileStorage, level_test_dao: LevelTestingData,
    telegraph: Telegraph,
):
    dp.update.middleware(ConfigMiddleware(bot_config))
    dp.update.middleware(InitMiddleware(
        pool=pool, user_getter=user_getter, dcf=dcf, redis=redis,
        scheduler=scheduler, locker=locker, file_storage=file_storage,
        level_test_dao=level_test_dao, telegraph=telegraph,
    ))
    dp.update.middleware(LoadDataMiddleware())
    dp.message.middleware(FixTargetMiddleware())
