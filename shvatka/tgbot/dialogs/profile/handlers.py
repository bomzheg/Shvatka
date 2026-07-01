from typing import Any

from dishka import FromDishka
from aiogram.types import Message
from aiogram_dialog import DialogManager
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.hasher import PasswordHasher
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.mail import EmailSender
from shvatka.core.players.player import set_player_username
from shvatka.core.services import email as email_service
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import validate_new_username, validate_email
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states


def validate_username(username: str) -> str:
    if new_username := validate_new_username(username):
        return new_username
    raise ValueError


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


def validate_email_input(email: str) -> str:
    if normalized := validate_email(email):
        return normalized
    raise ValueError


@inject
async def email_invalid(
    message: Message,
    __: Any,
    manager: DialogManager,
    error: ValueError,
) -> None:
    await message.reply("Некорректный адрес электронной почты, попробуй ещё раз")


@inject
async def on_email_entered(
    message: Message,
    __: Any,
    manager: DialogManager,
    email: str,
    identity: FromDishka[IdentityProvider],
    holder: FromDishka[HolderDao],
    hasher: FromDishka[PasswordHasher],
    sender: FromDishka[EmailSender],
) -> None:
    player = await identity.get_required_player()
    if await holder.email.is_email_occupied(email):
        await message.reply("Эта электронная почта уже используется, попробуй другую")
        return
    manager.dialog_data["email"] = email
    if not await holder.player.has_password(player):
        # a shared password is required to be able to log in by email later
        await manager.switch_to(state=states.ProfileSG.email_password)
        return
    await _send_and_go_to_code(message, manager, player, email, None, holder, hasher, sender)


@inject
async def on_email_password_entered(
    message: Message,
    __: Any,
    manager: DialogManager,
    password: str,
    identity: FromDishka[IdentityProvider],
    holder: FromDishka[HolderDao],
    hasher: FromDishka[PasswordHasher],
    sender: FromDishka[EmailSender],
) -> None:
    player = await identity.get_required_player()
    email = manager.dialog_data["email"]
    await _send_and_go_to_code(message, manager, player, email, password, holder, hasher, sender)


async def _send_and_go_to_code(
    message, manager, player, email, password, holder, hasher, sender
) -> None:
    try:
        await email_service.add_email_to_player(
            player=player,
            email=email,
            password=password,
            dao=holder.email,
            hasher=hasher,
            store=holder.email_confirm,
            sender=sender,
        )
    except exceptions.EmailAlreadyExist:
        await message.reply("Эта электронная почта уже используется, попробуй другую")
        await manager.switch_to(state=states.ProfileSG.main)
        return
    except exceptions.EmailInvalid:
        await message.reply("Некорректный адрес электронной почты")
        await manager.switch_to(state=states.ProfileSG.main)
        return
    await message.reply("На указанную почту отправлен код подтверждения")
    await manager.switch_to(state=states.ProfileSG.email_code)


@inject
async def on_email_code_entered(
    message: Message,
    __: Any,
    manager: DialogManager,
    code: str,
    holder: FromDishka[HolderDao],
) -> None:
    email = manager.dialog_data["email"]
    try:
        await email_service.confirm_email(
            email=email,
            code=code,
            dao=holder.email,
            store=holder.email_confirm,
        )
    except exceptions.EmailConfirmationCodeInvalid:
        await message.reply("Неверный или устаревший код, попробуй ещё раз")
        return
    await message.reply("Электронная почта успешно подтверждена ✅")
    await manager.switch_to(state=states.ProfileSG.main)
