from typing import Any

from dishka import FromDishka
from aiogram.types import Message
from aiogram_dialog import DialogManager
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.players.player import set_player_username
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def save_new_username(
    message: Message,
    __: Any,
    ___: DialogManager,
    new_username: str,
    identity: FromDishka[IdentityProvider],
    holder: FromDishka[HolderDao],
) -> None:
    player = await identity.get_required_player()
    try:
        await set_player_username(player, new_username, holder.player)
    except exceptions.PlayerUsernameOccupied:
        await message.reply("Это имя пользователя уже кем-то занято, попробуй другое")