from aiogram import Router

from src.tgbot.filters import GameStatusFilter


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
