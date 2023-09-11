import json
import logging
import typing
from functools import partial

from aiogram import Dispatcher, Bot
from aiogram.exceptions import AiogramError
from aiogram.filters import ExceptionTypeFilter
from aiogram.types.error_event import ErrorEvent
from aiogram.utils.markdown import html_decoration as hd
from aiogram_dialog.api.exceptions import UnknownIntent

from shvatka.core.utils.exceptions import SHError

logger = logging.getLogger(__name__)


async def handle_sh_error(error: ErrorEvent, log_chat_id: int, bot: Bot):
    exception: SHError = typing.cast(SHError, error.exception)
    if c := error.update.callback_query:
        await c.answer(exception.notify_user, show_alert=True)
    else:
        chat_id = exception.chat_id or exception.user_id
        if chat_id is None and exception.chat:
            chat_id = exception.chat.tg_id
        if chat_id is None and exception.user:
            chat_id = exception.user.tg_id
        if chat_id is None and exception.player:
            chat_id = exception.player.get_chat_id()
        if chat_id:
            try:
                await bot.send_message(chat_id=chat_id, text=f"Произошла ошибка\n{exception}")
            except AiogramError as e:
                logger.exception("can't send error message to user", exc_info=e)

    await handle(error=error, log_chat_id=log_chat_id, bot=bot)


async def clear_unknown_intent(error: ErrorEvent, bot: Bot):
    assert error.update.callback_query
    assert error.update.callback_query.message
    await bot.edit_message_reply_markup(
        chat_id=error.update.callback_query.message.chat.id,
        message_id=error.update.callback_query.message.message_id,
        reply_markup=None,
    )


async def handle(error: ErrorEvent, log_chat_id: int, bot: Bot):
    logger.exception(
        "Cause unexpected exception %s, by processing %s",
        error.exception.__class__.__name__,
        error.update.dict(exclude_none=True),
        exc_info=error.exception,
    )
    if not log_chat_id:
        return
    await bot.send_message(
        log_chat_id,
        f"Получено исключение {hd.quote(str(error.exception))}\n"
        f"во время обработки апдейта "
        f"{hd.quote(json.dumps(error.update.dict(exclude_none=True), default=str)[:3500])}\n",
    )


def setup(dp: Dispatcher, log_chat_id: int):
    dp.errors.register(
        partial(handle_sh_error, log_chat_id=log_chat_id), ExceptionTypeFilter(SHError)
    )
    dp.errors.register(clear_unknown_intent, ExceptionTypeFilter(UnknownIntent))
    dp.errors.register(partial(handle, log_chat_id=log_chat_id))
