from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shvatka.core.models import dto
from shvatka.tgbot.services.inline_data import InlineData


class AddGameOrgID(InlineData, prefix="add_game_org"):
    game_manage_token: str
    game_id: int


class AgreeBeOrgCD(CallbackData, prefix="agree_be_org"):
    token: str
    inviter_id: int
    is_agreement: bool


def get_kb_agree_be_org(token: str, inviter: dto.Player) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Да",
        callback_data=AgreeBeOrgCD(token=token, is_agreement=True, inviter_id=inviter.id),
    )
    builder.button(
        text="Нет",
        callback_data=AgreeBeOrgCD(token=token, is_agreement=False, inviter_id=inviter.id),
    )
    builder.adjust(2)
    return builder.as_markup()
