from aiogram import Router
from aiogram.filters import Command

from shvatka.tgbot import states
from shvatka.tgbot.utils.router import register_start_handler
from shvatka.tgbot.views.commands import GAMES_COMMAND


def setup() -> Router:
    router = Router(name=__name__)
    register_start_handler(
        Command(GAMES_COMMAND),
        state=states.CompletedGamesPanelSG.list,
        router=router,
    )
    return router
