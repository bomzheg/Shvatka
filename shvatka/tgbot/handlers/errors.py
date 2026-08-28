import json
import logging
import typing
from functools import partial

from aiogram import Bot, Dispatcher
from aiogram.exceptions import AiogramError, TelegramBadRequest
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import InlineKeyboardMarkup
from aiogram.types.error_event import ErrorEvent
from aiogram.utils.markdown import html_decoration as hd
from aiogram_dialog.api.exceptions import UnknownIntent

from shvatka.common.docs import DocsUrlFactory
from shvatka.core.utils.exceptions import SHError
from shvatka.tgbot.views.docs_link import error_doc_link

logger = logging.getLogger(__name__)

MESSAGE_IS_NOT_MODIFIED = "message is not modified"


def is_message_not_modified(error: ErrorEvent) -> bool:
    exception = error.exception
    return (
        isinstance(exception, TelegramBadRequest) and MESSAGE_IS_NOT_MODIFIED in exception.message
    )


async def ignore_message_not_modified(error: ErrorEvent) -> None:
    logger.debug("Ignoring %s", error.exception)
    if c := error.update.callback_query:
        await c.answer()


async def handle_sh_error(error: ErrorEvent, log_chat_id: int, docs: DocsUrlFactory, bot: Bot):
    exception: SHError = typing.cast(SHError, error.exception)
    doc_link = error_doc_link(exception, docs)
    chat_id = find_chat_id(error, exception)
    if c := error.update.callback_query:
        await c.answer(exception.notify_user, show_alert=True)
        # an alert holds no link, so the documentation goes as a message of its own
        if doc_link and chat_id:
            await notify_user(bot, chat_id, doc_link)
    elif chat_id:
        text = f"Произошла ошибка\n{exception}"
        if doc_link:
            text = f"{text}\n\n{doc_link}"
        await notify_user(bot, chat_id, text)

    await handle(error=error, log_chat_id=log_chat_id, bot=bot)


def find_chat_id(error: ErrorEvent, exception: SHError) -> int | None:
    """Where to write to the user who caused the error."""
    if (c := error.update.callback_query) is not None and c.message is not None:
        return c.message.chat.id
    if chat_id := (exception.chat_id or exception.user_id):
        return chat_id
    if exception.chat:
        return exception.chat.tg_id
    if exception.user:
        return exception.user.tg_id
    if exception.player:
        return exception.player.get_chat_id()
    return None


async def notify_user(bot: Bot, chat_id: int, text: str) -> None:
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except AiogramError as e:
        logger.warning("can't send error message to user", exc_info=e)


async def clear_unknown_intent(error: ErrorEvent, bot: Bot):
    assert error.update.callback_query
    assert error.update.callback_query.message
    await bot.edit_message_reply_markup(
        chat_id=error.update.callback_query.message.chat.id,
        message_id=error.update.callback_query.message.message_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[]),
    )


async def handle(error: ErrorEvent, log_chat_id: int, bot: Bot):
    logger.exception(
        "Cause unexpected exception %s, by processing %s",
        error.exception.__class__.__name__,
        error.update.model_dump(exclude_none=True),
        exc_info=error.exception,
    )
    if not log_chat_id:
        return
    error_text = hd.quote(
        json.dumps(error.update.model_dump(exclude_none=True), default=str)[:3500]
    )
    await bot.send_message(
        log_chat_id,
        f"Получено исключение {hd.quote(str(error.exception))}\n"
        f"во время обработки апдейта "
        f"{error_text}\n",
    )


def setup(dp: Dispatcher, log_chat_id: int, docs: DocsUrlFactory):
    dp.errors.register(
        partial(handle_sh_error, log_chat_id=log_chat_id, docs=docs),
        ExceptionTypeFilter(SHError),
    )
    dp.errors.register(clear_unknown_intent, ExceptionTypeFilter(UnknownIntent))
    dp.errors.register(ignore_message_not_modified, is_message_not_modified)
    dp.errors.register(partial(handle, log_chat_id=log_chat_id))
