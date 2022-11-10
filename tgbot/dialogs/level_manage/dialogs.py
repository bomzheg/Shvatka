from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel
from aiogram_dialog.widgets.text import Const, Format

from tgbot.states import LevelManageSG
from .getters import get_level_id
from .handlers import edit_level, show_level

level_manage = Dialog(
    Window(
        Format("Уровень <b>{level.name_id}</b>"),
        Button(
            Const("Редактирование"),
            id="level_edit",
            on_click=edit_level,
        ),
        Button(
            Const("Показать"),
            id="level_show",
            on_click=show_level,
        ),
        Cancel(Const("Назад")),
        state=LevelManageSG.menu,
        getter=get_level_id,
    ),
)
