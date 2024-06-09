
from aiogram import Router, Dispatcher
from aiogram.dispatcher.event.handler import CallbackType
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
    *filters: CallbackType,
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


def print_router_tree(router: Router, indent: int = 0) -> str:
    if isinstance(router, Dispatcher):
        result = " " * indent + "dispatcher"
    else:
        result = " " * indent + router.name
    for in_router in router.sub_routers:
        result += "\n" + print_router_tree(in_router, indent + 2)
    return result
