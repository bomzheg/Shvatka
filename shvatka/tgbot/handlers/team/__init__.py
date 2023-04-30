from aiogram import Router

from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.utils.router import disable_router_on_game
from . import info
from . import manage


def setup(bot_config: BotConfig) -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)
    router.include_router(manage.setup(bot_config))
    router.include_router(info.setup())
    return router
