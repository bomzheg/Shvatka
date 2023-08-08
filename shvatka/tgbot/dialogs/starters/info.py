from aiogram import Router
from aiogram.filters import Command

from shvatka.tgbot import states
from shvatka.tgbot.utils.router import register_start_handler
from shvatka.tgbot.views.commands import TEAMS_COMMAND


def setup() -> Router:
    router = Router(name=__name__)
    register_start_handler(
        Command(commands=TEAMS_COMMAND),
        state=states.TeamsSg.list,
        router=router,
    )
    return router
