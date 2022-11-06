from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format

from tgbot.states import LevelSG
from .getters import get_time_hints
from .handlers import process_result, start_add_time_hint

level = Dialog(
    Window(
        Const("Подсказки"),
        Format("сейчас есть {time_hints_count}"),
        Button(Const("Добавить"), id="add_time_hint", on_click=start_add_time_hint),
        state=LevelSG.time_hints,
        getter=get_time_hints,
    ),
    on_process_result=process_result,
)
