from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command

from shvatka.tgbot import states
from shvatka.tgbot.utils.router import disable_router_on_game, register_start_handler
from shvatka.tgbot.views.commands import GAMES_COMMAND


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)
    register_start_handler(
        Command(GAMES_COMMAND),
        F.chat.type == ChatType.PRIVATE,
        state=states.CompletedGamesPanelSG.list,
        router=router,
    )
    return router
