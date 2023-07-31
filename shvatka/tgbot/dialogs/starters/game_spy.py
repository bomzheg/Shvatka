from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command

from shvatka.tgbot import states
from shvatka.tgbot.filters import GameStatusFilter
from shvatka.tgbot.utils.router import register_start_handler
from shvatka.tgbot.views.commands import SPY_COMMAND, SPY_LEVELS_COMMAND, SPY_KEYS_COMMAND


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(GameStatusFilter(running=True))
    register_start_handler(
        F.chat.type == ChatType.PRIVATE,
        Command(commands=SPY_COMMAND),
        state=states.OrgSpySG.main,
        router=router,  # TODO is_org
    )
    register_start_handler(
        Command(commands=SPY_LEVELS_COMMAND),  # TODO is_org
        F.chat.type == ChatType.PRIVATE,
        state=states.OrgSpySG.spy,
        router=router,
    )
    register_start_handler(
        Command(commands=SPY_KEYS_COMMAND),  # TODO is_org
        F.chat.type == ChatType.PRIVATE,
        state=states.OrgSpySG.keys,
        router=router,
    )
    return router
