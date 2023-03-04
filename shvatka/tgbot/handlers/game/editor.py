import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import StartMode, DialogManager

from shvatka.tgbot import states
from shvatka.tgbot.filters.can_be_author import can_be_author
from shvatka.tgbot.utils.router import disable_router_on_game
from shvatka.tgbot.views.commands import MY_GAMES_COMMAND, NEW_LEVEL_COMMAND, NEW_GAME_COMMAND

logger = logging.getLogger(__name__)


async def get_manage(_: Message, dialog_manager: DialogManager):
    await dialog_manager.start(states.MyGamesPanelSG.choose_game, mode=StartMode.RESET_STACK)


async def get_level_editor(_: Message, dialog_manager: DialogManager):
    await dialog_manager.start(states.LevelSG.level_id, mode=StartMode.RESET_STACK)


async def get_game_editor(_: Message, dialog_manager: DialogManager):
    await dialog_manager.start(states.GameWriteSG.game_name, mode=StartMode.RESET_STACK)


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)
    router.message.filter(
        can_be_author,
    )

    router.message.register(get_manage, Command(commands=MY_GAMES_COMMAND))
    router.message.register(get_level_editor, Command(commands=NEW_LEVEL_COMMAND))
    router.message.register(get_game_editor, Command(commands=NEW_GAME_COMMAND))
    return router
