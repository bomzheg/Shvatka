from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.identity import IdentityProvider


@inject
async def can_be_author(_: Message, identity: FromDishka[IdentityProvider]) -> bool:
    player = await identity.get_player()
    return player is not None and player.can_be_author
