from typing import Protocol

from aiogram.types import CallbackQuery
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.identity import IdentityProvider


class InviterCD(Protocol):
    inviter_id: int


@inject
async def is_inviter(
    _: CallbackQuery,
    callback_data: InviterCD,
    identity: FromDishka[IdentityProvider],
) -> bool:
    """Whether the player who clicked is the one who sent the invite."""
    player = await identity.get_player()
    return player is not None and callback_data.inviter_id == player.id
