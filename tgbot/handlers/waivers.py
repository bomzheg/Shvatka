from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from tgbot.filters.game_status import GameStatusFilter


async def start_waivers(m: Message):
    pass


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(
        GameStatusFilter(running=False),
    )
    router.message.register(start_waivers, Command("waivers"))
    return router
