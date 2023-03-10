from aiogram import Router
from aiogram.filters import Filter
from aiogram.fsm.state import State
from aiogram.types import Message
from aiogram_dialog import StartMode, DialogManager

from shvatka.tgbot.filters import GameStatusFilter


def disable_router_on_game(router: Router):
    router.message.filter(
        GameStatusFilter(running=False),
    )
    router.callback_query.filter(
        GameStatusFilter(running=False),
    )
    router.inline_query.filter(
        GameStatusFilter(running=False),
    )


def register_start_handler(
    *filters: Filter,
    state: State,
    router: Router,
    mode: StartMode = StartMode.NORMAL,
):
    async def start_dialog(
        message: Message,
        dialog_manager: DialogManager,
    ) -> None:
        await dialog_manager.start(state, mode=mode)

    router.message.register(
        start_dialog,
        *filters,
    )
