from functools import partial

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from tgbot.config.models.bot import BotConfig
from tgbot.filters.superusers import is_superuser
from tgbot.views.commands import UPDATE_COMMANDS, GET_OUT


async def exception(message: Message):
    raise RuntimeError(message.text)


async def leave_chat(message: Message, bot: Bot):
    await bot.leave_chat(message.chat.id)


def setup(bot_config: BotConfig) -> Router:
    router = Router(name=__name__)
    is_superuser_ = partial(is_superuser, superusers=bot_config.superusers)

    router.message.register(exception, is_superuser_, Command(commands=UPDATE_COMMANDS.command))
    router.message.register(leave_chat, is_superuser_, Command(commands=GET_OUT.command))
    return router
