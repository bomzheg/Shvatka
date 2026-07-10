from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ActionRequestCD(CallbackData, prefix="act_req"):
    request_id: int
    accept: bool


def get_action_request_kb(request_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Принять", callback_data=ActionRequestCD(request_id=request_id, accept=True)
    )
    builder.button(
        text="Отклонить", callback_data=ActionRequestCD(request_id=request_id, accept=False)
    )
    builder.adjust(2)
    return builder.as_markup()
