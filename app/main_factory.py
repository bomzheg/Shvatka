import os
from pathlib import Path

from aiogram import Bot, Dispatcher

from app.handlers import setup_handlers
from app.middlewares import setup_middlewares
from app.models.config import Config
from app.models.config.main import Paths
from app.models.db import create_pool
from app.services.username_resolver.user_getter import UserGetter


def create_bot(config: Config) -> Bot:
    return Bot(
        token=config.bot.token,
        parse_mode="HTML",
        session=config.bot.create_session(),
    )


def create_dispatcher(config: Config, user_getter: UserGetter) -> Dispatcher:
    dp = Dispatcher(storage=(config.storage.create_storage()))
    setup_middlewares(dp, create_pool(config.db), config.bot, user_getter)
    setup_handlers(dp, config.bot)
    return dp


def get_paths() -> Paths:
    if path := os.getenv("BOT_PATH"):
        return Paths(Path(path))
    return Paths(Path(__file__).parent.parent)
