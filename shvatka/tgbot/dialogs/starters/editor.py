import logging

from aiogram import Router
from aiogram.filters import Command

from shvatka.tgbot import states
from shvatka.tgbot.filters.can_be_author import can_be_author
from shvatka.tgbot.utils.router import register_start_handler
from shvatka.tgbot.views.commands import (
    MY_GAMES_COMMAND,
    NEW_LEVEL_COMMAND,
    NEW_GAME_COMMAND,
    LEVELS_COMMAND,
)

logger = logging.getLogger(__name__)


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(
        can_be_author,
    )
    register_start_handler(
        Command(commands=MY_GAMES_COMMAND),
        state=states.MyGamesPanelSG.choose_game,
        router=router,
    )
    register_start_handler(
        Command(commands=NEW_LEVEL_COMMAND),
        state=states.LevelSG.level_id,
        router=router,
    )
    register_start_handler(
        Command(commands=LEVELS_COMMAND),
        state=states.LevelListSG.levels,
        router=router,
    )
    register_start_handler(
        Command(commands=NEW_GAME_COMMAND),
        state=states.GameWriteSG.game_name,
        router=router,
    )
    return router
