from aiogram.types import Message


async def is_superuser(message: Message, superusers: list[int]) -> bool:
    return message.from_user.id in superusers
