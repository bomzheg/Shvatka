from aiogram import Dispatcher, Bot
from aiogram.types import Message
from functools import partial

from app.filters.superusers import is_superuser
from app.models.config.main import BotConfig


async def exception(message: Message):
    raise RuntimeError(message.text)


async def leave_chat(message: Message, bot: Bot):
    await bot.leave_chat(message.chat.id)


def setup_superuser(dp: Dispatcher, bot_config: BotConfig):
    is_superuser_ = partial(is_superuser, superusers=bot_config.superusers)

    dp.message.register(exception, is_superuser_, commands="exception")
    dp.message.register(leave_chat, is_superuser_, commands="get_out")
