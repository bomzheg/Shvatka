from aiogram import Bot
from aiogram_dialog.widgets.text import setup_jinja as setup_jinja_internal

from shvatka.tgbot.views.player import get_emoji
from .boolean_emoji import bool_render
from .game_status import to_readable_name
from .timezone import datetime_filter, timedelta_filter


def setup_jinja(bot: Bot):
    setup_jinja_internal(
        bot,
        filters={
            "user_timezone": datetime_filter,
            "player_emoji": get_emoji,
            "bool_emoji": bool_render,
            "game_status": to_readable_name,
            "timedelta": timedelta_filter,
        },
    )
