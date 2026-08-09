import logging

from aiogram import Dispatcher
from aiogram_dialog.api.protocols import MessageManagerProtocol, BgManagerFactory

from shvatka.tgbot import dialogs
from shvatka.tgbot.config.models.main import TgBotConfig
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
    action_request,
    member_tags,
)

logger = logging.getLogger(__name__)


def setup_handlers(
    dp: Dispatcher, config: TgBotConfig, message_manager: MessageManagerProtocol
) -> BgManagerFactory:
    errors.setup(dp, config.bot.log_chat)
    dp.include_router(base.setup())
    dp.include_router(superuser.setup(config.superusers))
    dp.include_router(player.setup())
    dp.include_router(team.setup())
    dp.include_router(action_request.setup())
    dp.include_router(merge.setup(config.superusers))
    dp.include_router(game.setup())
    dp.include_router(waivers.setup())
    dp.include_router(admin.setup(config.superusers))
    dp.include_router(capcha.setup(config.bot))
    dp.include_router(member_tags.setup(config.bot))

    bg_manager_factory = dialogs.setup(dp, message_manager)

    # always must be last registered
    dp.include_router(last.setup())
    logger.debug("handlers configured successfully")
    return bg_manager_factory
