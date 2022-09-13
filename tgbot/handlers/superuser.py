from functools import partial

from aiogram import Dispatcher, Bot
from aiogram.filters import Command
from aiogram.types import Message

from shvatka.models.config.main import BotConfig
from shvatka.views.commands import UPDATE_COMMANDS, GET_OUT
from tgbot.filters.superusers import is_superuser


async def exception(message: Message):
    raise RuntimeError(message.text)


async def leave_chat(message: Message, bot: Bot):
    await bot.leave_chat(message.chat.id)


def setup(dp: Dispatcher, bot_config: BotConfig):
    is_superuser_ = partial(is_superuser, superusers=bot_config.superusers)

    dp.message.register(exception, is_superuser_, Command(commands=UPDATE_COMMANDS.command))
    dp.message.register(leave_chat, is_superuser_, Command(commands=GET_OUT.command))
