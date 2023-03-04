from aiogram.types import Message

from src.core.models import dto


async def can_be_author(_: Message, player: dto.Player):
    return player.can_be_author
