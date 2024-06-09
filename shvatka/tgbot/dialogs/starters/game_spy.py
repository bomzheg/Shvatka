from aiogram import Router
from aiogram.filters import Command

from shvatka.tgbot import states
from shvatka.tgbot.filters.is_org import OrgFilter
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
        OrgFilter(only_for_running_game=False),
        state=states.OrgSpySG.main,
        router=router,
    )
    register_start_handler(
        Command(commands=START_COMMAND),
        OrgFilter(),
        state=states.OrgSpySG.main,
        router=router,
    )
    register_start_handler(
        Command(commands=SPY_LEVELS_COMMAND),
        OrgFilter(can_spy=True),
        state=states.OrgSpySG.spy,
        router=router,
    )
    register_start_handler(
        Command(commands=SPY_KEYS_COMMAND),
        OrgFilter(can_see_log_keys=True),
        state=states.OrgSpySG.keys,
        router=router,
    )
    return router
