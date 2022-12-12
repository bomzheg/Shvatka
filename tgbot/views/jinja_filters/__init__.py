from aiogram import Bot
from aiogram_dialog.widgets.text import setup_jinja as setup_jinja_internal

from tgbot.views.jinja_filters.timezone import datetime_filter
from tgbot.views.player import get_emoji


def setup_jinja(bot: Bot):
    setup_jinja_internal(
        bot,
        filters={
            "user_timezone": datetime_filter,
            "player_emoji": get_emoji,
        },
    )
