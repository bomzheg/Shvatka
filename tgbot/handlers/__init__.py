import logging

from aiogram import Dispatcher
from aiogram_dialog import DialogRegistry

from tgbot.config.models.bot import BotConfig
from tgbot.dialogs import setup_dialogs
from tgbot.handlers import base, game, waivers
from tgbot.handlers import errors
from tgbot.handlers import last
from tgbot.handlers import superuser
from tgbot.handlers import team

logger = logging.getLogger(__name__)


def setup_handlers(dp: Dispatcher, bot_config: BotConfig):
    errors.setup(dp, bot_config.log_chat)
    dp.include_router(base.setup())
    dp.include_router(superuser.setup(bot_config))

    registry = DialogRegistry(dp)
    setup_dialogs(registry)

    dp.include_router(team.setup())
    dp.include_router(game.setup())
    dp.include_router(waivers.setup())

    # always must be last registered
    dp.include_router(last.setup())
    logger.debug("handlers configured successfully")
