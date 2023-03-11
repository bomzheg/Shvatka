from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Jinja, Const

from shvatka.tgbot import states
from .getters import player_getter

player_dialog = Dialog(
    Window(
        Jinja(
            "Игрок {{player.name_mention}}"
        ),
        Cancel(Const("⤴Выход")),
        getter=player_getter,
        state=states.PlayerSg.main,
    ),
)
