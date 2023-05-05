from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shvatka.core.models import dto


class TeamMergeCD(CallbackData, prefix="team_merge"):
    primary_team_id: int
    secondary_team_id: int


class PlayerMergeCD(CallbackData, prefix="player_merge"):
    primary_player_id: int
    secondary_player_id: int


def get_team_merge_confirm_kb(primary: dto.Team, secondary: dto.Team) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Подтвердить слияние",
        callback_data=TeamMergeCD(primary_team_id=primary.id, secondary_team_id=secondary.id),
    )
    return builder.as_markup()


def get_player_merge_confirm_kb(primary: dto.Player, secondary: dto.Player):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Подтвердить слияние",
        callback_data=PlayerMergeCD(
            primary_player_id=primary.id, secondary_player_id=secondary.id
        ),
    )
    return builder.as_markup()
