import logging

from aiogram import Dispatcher
from aiogram_dialog import DialogRegistry

from shvatka.tgbot import dialogs
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.handlers import errors
from shvatka.tgbot.handlers import game, waivers, player
from shvatka.tgbot.handlers import last
from shvatka.tgbot.handlers import superuser, base
from shvatka.tgbot.handlers import team

logger = logging.getLogger(__name__)


def setup_handlers(dp: Dispatcher, bot_config: BotConfig, registry: DialogRegistry):
    errors.setup(dp, bot_config.log_chat)
    dp.include_router(base.setup())
    dp.include_router(superuser.setup(bot_config))
    dp.include_router(player.setup())
    dp.include_router(team.setup(bot_config))
    dp.include_router(game.setup())
    dp.include_router(waivers.setup())

    dialogs.setup(registry, dp)

    # always must be last registered
    dp.include_router(last.setup())
    logger.debug("handlers configured successfully")
