from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager

from tgbot.states import MainMenu
from tgbot.views.commands import START_COMMAND


async def main_menu(m: Message, dialog_manager: DialogManager):
    await dialog_manager.start(MainMenu.main)


def setup() -> Router:
    router = Router(name=__name__)
    router.message.register(main_menu, Command(START_COMMAND))
    return router
