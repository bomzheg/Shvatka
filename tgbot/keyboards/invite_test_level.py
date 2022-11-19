from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shvatka.models import dto


class LevelTestInviteCD(CallbackData, prefix="level_test_invite"):
    level_id: int
    org_id: int


def get_kb_level_test_invite(level: dto.Level, org: dto.SecondaryOrganizer) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Тестировать сейчас", callback_data=LevelTestInviteCD(level_id=level.db_id, org_id=org.id))
    return builder.as_markup()
