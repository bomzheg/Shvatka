import json
import logging
import typing
from functools import partial

from aiogram import Dispatcher, Bot
from aiogram.exceptions import AiogramError
from aiogram.filters import ExceptionTypeFilter
from aiogram.types.error_event import ErrorEvent
from aiogram.utils.markdown import html_decoration as hd

from shvatka.utils.exceptions import SHError

logger = logging.getLogger(__name__)


async def handle_sh_error(error: ErrorEvent, log_chat_id: int, bot: Bot):
    exception: SHError = typing.cast(SHError, error.exception)
    chat_id = exception.chat_id or exception.user_id
    if chat_id is None and exception.chat:
        chat_id = exception.chat.tg_id
    if chat_id is None and exception.user:
        chat_id = exception.user.tg_id
    if chat_id is None and exception.player and exception.player.user:
        chat_id = exception.player.user.tg_id
    if chat_id:
        try:
            await bot.send_message(
                chat_id=chat_id, text=f"Произошла ошибка\n{exception}"
            )
        except AiogramError as e:
            logger.exception("can't send error message to user", exc_info=e)

    await handle(error=error, log_chat_id=log_chat_id, bot=bot)


async def handle(error: ErrorEvent, log_chat_id: int, bot: Bot):
    logger.exception(
        "Cause unexpected exception %s, by processing %s",
        error.exception.__class__.__name__, error.update.dict(exclude_none=True), exc_info=error.exception,
    )
    if not log_chat_id:
        return
    await bot.send_message(
        log_chat_id,
        f"Получено исключение {hd.quote(str(error.exception))}\n"
        f"во время обработки апдейта "
        f"{hd.quote(json.dumps(error.update.dict(exclude_none=True), default=str))}\n"
    )


def setup(dp: Dispatcher, log_chat_id: int):
    dp.errors.register(
        partial(handle_sh_error, log_chat_id=log_chat_id),
        ExceptionTypeFilter(SHError)
    )
    dp.errors.register(
        partial(handle, log_chat_id=log_chat_id)
    )
