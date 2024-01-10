import asyncio
import logging
from functools import partial

from aiogram import Bot, Router
from aiogram.enums import BotCommandScopeType
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import Message, BotCommandScopeChat

from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.version import get_version
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.filters.superusers import is_superuser
from shvatka.tgbot.views.commands import (
    GET_OUT,
    EXCEPTION_COMMAND,
    UPDATE_COMMANDS,
    VERSION_COMMAND,
)

logger = logging.getLogger(__name__)


async def exception(message: Message):
    raise RuntimeError(message.text)


async def leave_chat(message: Message, bot: Bot):
    await bot.leave_chat(message.chat.id)


async def clean_commands_menu_handler(message: Message, bot: Bot, dao: HolderDao):
    offset = 0
    limit = 20
    while True:
        offset += limit
        users = await dao.user.get_page(offset, limit)
        if not users:
            break
        for user in users:
            try:
                await bot.delete_my_commands(
                    scope=BotCommandScopeChat(chat_id=user.tg_id, type=BotCommandScopeType.CHAT)
                )
            except TelegramAPIError as e:
                logger.error("some error with delete scope", exc_info=e)
            else:
                logger.debug("updated scope for %s", user.tg_id)
            await asyncio.sleep(1)
    await message.answer("обновлено!")


async def version_handler(message: Message, main_config: TgBotConfig):
    version = get_version(main_config.paths)
    await message.answer(f"Дата билда: {version.build_at}\nВерсия: {version.vcs_hash}")


def setup(bot_config: BotConfig) -> Router:
    router = Router(name=__name__)
    is_superuser_ = partial(is_superuser, superusers=bot_config.superusers)
    router.message.filter(is_superuser_)

    router.message.register(exception, Command(commands=EXCEPTION_COMMAND))
    router.message.register(leave_chat, Command(commands=GET_OUT))
    router.message.register(clean_commands_menu_handler, Command(commands=UPDATE_COMMANDS))
    router.message.register(version_handler, Command(commands=VERSION_COMMAND))
    return router
