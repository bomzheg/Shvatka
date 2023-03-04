from aiogram import types
from aiogram.types import Message


async def is_superuser(message: Message, superusers: list[int]) -> bool:
    assert isinstance(message.from_user, types.User)
    return message.from_user.id in superusers
