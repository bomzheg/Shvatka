from aiogram import Dispatcher
from dataclass_factory import Factory
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from shvatka.models.config.main import BotConfig
from shvatka.scheduler import Scheduler
from shvatka.services.username_resolver.user_getter import UserGetter
from shvatka.utils.key_checker_lock import KeyCheckerFactory
from tgbot.middlewares.config_middleware import ConfigMiddleware
from tgbot.middlewares.data_load_middleware import LoadDataMiddleware
from tgbot.middlewares.fix_target_middleware import FixTargetMiddleware
from tgbot.middlewares.init_middleware import InitMiddleware


def setup_middlewares(
    dp: Dispatcher, pool: sessionmaker, bot_config: BotConfig,
    user_getter: UserGetter, dcf: Factory, redis: Redis, scheduler: Scheduler,
    locker: KeyCheckerFactory,
):
    dp.update.middleware(ConfigMiddleware(bot_config))
    dp.update.middleware(InitMiddleware(
        pool=pool, user_getter=user_getter, dcf=dcf, redis=redis,
        scheduler=scheduler, locker=locker,
    ))
    dp.update.middleware(LoadDataMiddleware())
    dp.message.middleware(FixTargetMiddleware())
