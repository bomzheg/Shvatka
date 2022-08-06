from aiogram import Router, Dispatcher
from aiogram.types import Message

router = Router(name=__name__)


async def save_game(m: Message):
    """TODO refactor it =)"""


def setup(dp: Dispatcher):
    dp.include_router(router)
