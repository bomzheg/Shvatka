from aiogram import Bot
from aiogram_dialog.widgets.text import setup_jinja as setup_jinja_internal

from shvatka.core.utils.datetime_utils import TIME_FORMAT
from shvatka.tgbot.views.player import get_emoji
from .boolean_emoji import bool_render
from .game_status import to_readable_name
from .timezone import datetime_filter, timedelta_filter
from ..utils import render_single_hint, render_hints, render_time_hint, render_time_hints


def setup_jinja(bot: Bot):
    setup_jinja_internal(
        bot,
        filters={
            "user_timezone": datetime_filter,
            "time_user_timezone": lambda x: datetime_filter(x, TIME_FORMAT),
            "player_emoji": get_emoji,
            "bool_emoji": bool_render,
            "game_status": to_readable_name,
            "timedelta": timedelta_filter,
            "single_hint": render_single_hint,
            "hints": render_hints,
            "time_hint": render_time_hint,
            "time_hints": render_time_hints,
        },
    )
