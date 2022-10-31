from contextlib import suppress

from aiogram import Bot
from aiogram.exceptions import AiogramError
from aiogram.utils.text_decorations import html_decoration as hd


async def total_remove_msg(bot: Bot, chat_id: int = None, msg_id: int = None, inline_msg_id: int = None):
    if inline_msg_id:
        return await edit_message_as_removed(bot, inline_message_id=inline_msg_id)
    if msg_id is None:
        return
    try:
        await bot.delete_message(chat_id, msg_id)
    except AiogramError:
        await edit_message_as_removed(bot, chat_id=chat_id, message_id=msg_id)


async def edit_message_as_removed(bot, inline_message_id=None, chat_id=None, message_id=None, text="(удалено)"):
    with suppress(AiogramError):
        return await bot.edit_message_text(
            text=hd.italic(text),
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            reply_markup=None
        )
