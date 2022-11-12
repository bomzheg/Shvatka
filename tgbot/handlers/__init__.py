import logging

from aiogram import Dispatcher

from tgbot.config.models.bot import BotConfig
from tgbot.handlers import base, game, waivers
from tgbot.handlers import errors
from tgbot.handlers import last
from tgbot.handlers import superuser
from tgbot.handlers import team
from tgbot.handlers.game import add_organizer

logger = logging.getLogger(__name__)


def setup_handlers(dp: Dispatcher, bot_config: BotConfig):
    errors.setup(dp, bot_config.log_chat)
    dp.include_router(base.setup())
    dp.include_router(superuser.setup(bot_config))

    dp.include_router(add_organizer.setup())
    dp.include_router(game.setup())

    # registry = DialogRegistry(dp)
    # setup_dialogs(registry)

    dp.include_router(team.setup())
    dp.include_router(waivers.setup())

    # always must be last registered
    dp.include_router(last.setup())
    logger.debug("handlers configured successfully")
