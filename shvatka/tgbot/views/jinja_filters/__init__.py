from collections.abc import Callable, Mapping

from aiogram import Bot
from aiogram_dialog.widgets.text import setup_jinja as setup_jinja_internal

from shvatka.core.views.texts import (
    render_effects,
    render_hints,
    render_single_hint,
    render_time_hint,
    render_time_hints,
)
from shvatka.tgbot.views.player import get_emoji

from .boolean_emoji import bool_render
from .game_status import to_readable_name
from .timezone import datetime_filter, time_user_timezone, timedelta_filter


def get_filters() -> Mapping[str, Callable[..., str]]:
    return {
        "user_timezone": datetime_filter,
        "time_user_timezone": time_user_timezone,
        "player_emoji": get_emoji,
        "bool_emoji": bool_render,
        "game_status": to_readable_name,
        "timedelta": timedelta_filter,
        "single_hint": render_single_hint,
        "hints": render_hints,
        "time_hint": render_time_hint,
        "time_hints": render_time_hints,
        "effects": render_effects,
    }


def setup_jinja(bot: Bot):
    setup_jinja_internal(
        bot,
        filters=get_filters(),
    )
