from aiogram import Bot

from src.shvatka.models import dto
from src.shvatka.models.enums.chat_type import ChatType


async def is_admin_filter(bot: Bot, chat: dto.Chat, user: dto.User) -> bool:
    if chat.type == ChatType.private:
        return False
    admins = await bot.get_chat_administrators(chat.tg_id)
    admins_id = {admin.user.id for admin in admins}
    return user.tg_id in admins_id
