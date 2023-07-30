import random

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestUser,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shvatka.core.models import dto


class JoinToTeamRequestCD(CallbackData, prefix="join_to_team"):
    team_id: int
    player_id: int
    y_n: bool


def get_join_team_kb(team: dto.Team, player: dto.Player) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Принять",
        callback_data=JoinToTeamRequestCD(team_id=team.id, player_id=player.id, y_n=True),
    )
    builder.button(
        text="Отказать",
        callback_data=JoinToTeamRequestCD(team_id=team.id, player_id=player.id, y_n=False),
    )
    builder.adjust(2)
    return builder.as_markup()


def get_user_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="ВЫБРАТЬ ИГРОКА В КОМАНДУ\n\n⏩НАЖАТЬ ПРЯМО СЮДА⏪",
                    request_user=KeyboardButtonRequestUser(
                        user_is_bot=False, request_id=random.randint(0, 1000)
                    ),
                )
            ]
        ]
    )
