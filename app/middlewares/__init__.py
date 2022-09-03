from aiogram import Dispatcher
from dataclass_factory import Factory
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from app.middlewares.config_middleware import ConfigMiddleware
from app.middlewares.data_load_middleware import LoadDataMiddleware
from app.middlewares.fix_target_middleware import FixTargetMiddleware
from app.middlewares.init_middleware import InitMiddleware
from app.models.config.main import BotConfig
from app.services.username_resolver.user_getter import UserGetter


def setup_middlewares(
    dp: Dispatcher, pool: sessionmaker, bot_config: BotConfig,
    user_getter: UserGetter, dcf: Factory, redis: Redis
):
    dp.update.middleware(ConfigMiddleware(bot_config))
    dp.update.middleware(InitMiddleware(pool, user_getter, dcf, redis))
    dp.update.middleware(LoadDataMiddleware())
    dp.message.middleware(FixTargetMiddleware())
