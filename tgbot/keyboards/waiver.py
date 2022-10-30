from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shvatka.models import dto
from shvatka.models.enums.played import Played


class WaiverCD(CallbackData, prefix="waiver_vote"):
    vote: Played
    team_id: int


def get_kb_waivers(team: dto.Team) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f'Играю', callback_data=WaiverCD(vote=Played.yes, team_id=team.id))
    builder.button(
        text=f'Не могу', callback_data=WaiverCD(vote=Played.no, team_id=team.id))
    builder.button(
        text=f'Думаю', callback_data=WaiverCD(vote=Played.think, team_id=team.id))
    builder.adjust(3)
    return builder.as_markup()
