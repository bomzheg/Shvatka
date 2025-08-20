import logging

from aiogram import Dispatcher
from aiogram_dialog.api.protocols import MessageManagerProtocol, BgManagerFactory

from shvatka.tgbot import dialogs
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.handlers import (
    errors,
    merge,
    admin,
    capcha,
    game,
    waivers,
    player,
    last,
    superuser,
    base,
    team,
)

logger = logging.getLogger(__name__)


def setup_handlers(
    dp: Dispatcher, bot_config: BotConfig, message_manager: MessageManagerProtocol
) -> BgManagerFactory:
    errors.setup(dp, bot_config.log_chat)
    dp.include_router(base.setup())
    dp.include_router(superuser.setup(bot_config))
    dp.include_router(player.setup())
    dp.include_router(team.setup())
    dp.include_router(merge.setup(bot_config))
    dp.include_router(game.setup())
    dp.include_router(waivers.setup())
    dp.include_router(admin.setup(bot_config))
    dp.include_router(capcha.setup(bot_config))

    bg_manager_factory = dialogs.setup(dp, message_manager)

    # always must be last registered
    dp.include_router(last.setup())
    logger.debug("handlers configured successfully")
    return bg_manager_factory
