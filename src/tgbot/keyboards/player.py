from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.shvatka.models import dto
from src.tgbot.services.inline_data import InlineData


class PromotePlayerID(InlineData, prefix="promote"):
    token: str


class AgreePromotionCD(CallbackData, prefix="agree_promotion"):
    token: str
    inviter_id: int
    is_agreement: bool


def get_kb_agree_promotion(token: str, inviter: dto.Player) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Да",
        callback_data=AgreePromotionCD(token=token, is_agreement=True, inviter_id=inviter.id),
    )
    builder.button(
        text="Нет",
        callback_data=AgreePromotionCD(token=token, is_agreement=False, inviter_id=inviter.id),
    )
    return builder.as_markup()
