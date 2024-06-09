from aiogram import Router
from aiogram.filters import Command

from shvatka.tgbot import states
from shvatka.tgbot.filters.is_org import is_org_on_running_game, is_org
from shvatka.tgbot.utils.router import register_start_handler
from shvatka.tgbot.views.commands import (
    SPY_COMMAND,
    SPY_LEVELS_COMMAND,
    SPY_KEYS_COMMAND,
    START_COMMAND,
)


def setup() -> Router:
    router = Router(name=__name__)
    register_start_handler(
        Command(commands=SPY_COMMAND),
        is_org,
        state=states.OrgSpySG.main,
        router=router,
    )
    register_start_handler(
        Command(commands=START_COMMAND),
        is_org_on_running_game,
        state=states.OrgSpySG.main,
        router=router,
    )
    register_start_handler(
        Command(commands=SPY_LEVELS_COMMAND),
        is_org,
        state=states.OrgSpySG.spy,
        router=router,
    )
    register_start_handler(
        Command(commands=SPY_KEYS_COMMAND),
        is_org,
        state=states.OrgSpySG.keys,
        router=router,
    )
    return router
