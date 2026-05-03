from typing import Any

from dishka import FromDishka
from aiogram.types import Message
from aiogram_dialog import DialogManager
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.players.player import set_player_username
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import validate_username_
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states


def validate_username(username: str) -> str:
    if not validate_username_(username):
        raise ValueError
    return username


@inject
async def username_invalid(
    message: Message,
    __: Any,
    manager: DialogManager,
    error: ValueError,
) -> None:
    await message.reply(
        "такое имя пользователя использовать нельзя. "
        "можно использовать a-z, A-Z, 0-9, _. "
        "длина от 3 до 50 символов"
    )


@inject
async def save_new_username(
    message: Message,
    __: Any,
    manager: DialogManager,
    new_username: str,
    identity: FromDishka[IdentityProvider],
    holder: FromDishka[HolderDao],
) -> None:
    player = await identity.get_required_player()
    try:
        await set_player_username(player, new_username, holder.player)
    except exceptions.PlayerUsernameOccupied:
        await message.reply("Это имя пользователя уже кем-то занято, попробуй другое")
    else:
        await manager.switch_to(state=states.ProfileSG.main)
