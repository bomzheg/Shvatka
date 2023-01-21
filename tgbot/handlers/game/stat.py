from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager

from tgbot import states
from tgbot.utils.router import disable_router_on_game
from tgbot.views.commands import GAMES_COMMAND


async def get_games_cmd(m: Message, dialog_manager: DialogManager):
    await dialog_manager.start(states.CompletedGamesPanelSG.list)


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)
    router.message.register(get_games_cmd, Command(GAMES_COMMAND))
    return router
