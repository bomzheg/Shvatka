import logging

import json
from aiogram import Dispatcher, Bot
from aiogram.types import Update
from functools import partial

from aiogram.utils.markdown import html_decoration as hd

logger = logging.getLogger(__name__)


async def handle(update: Update, exception: Exception, log_chat_id: int, bot: Bot):
    logger.exception(
        "Cause unexpected exception %s, by processing %s",
        exception.__class__.__name__, update.dict(exclude_none=True)
    )
    if not log_chat_id:
        return
    await bot.send_message(
        log_chat_id,
        f"Получено исключение {exception.__class__.__name__}\n"
        f"во время обработки апдейта {hd.quote(json.dumps(update.dict(exclude_none=True), default=str))}\n"
        f"{hd.quote(exception.args[0])}"
    )


def setup_errors(dp: Dispatcher, log_chat_id: int):
    dp.errors.register(partial(handle, log_chat_id=log_chat_id))
