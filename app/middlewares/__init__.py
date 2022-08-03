from aiogram import Dispatcher
from sqlalchemy.orm import sessionmaker

from app.middlewares.config_middleware import ConfigMiddleware
from app.middlewares.data_load_middleware import LoadDataMiddleware
from app.middlewares.db_middleware import DBMiddleware
from app.models.config.main import BotConfig


def setup_middlewares(dp: Dispatcher, pool: sessionmaker, bot_config: BotConfig):
    dp.update.middleware(ConfigMiddleware(bot_config))
    dp.update.middleware(DBMiddleware(pool))
    dp.update.middleware(LoadDataMiddleware())
