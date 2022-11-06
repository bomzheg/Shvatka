from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.text import Const, Format

from tgbot.states import TimeHintSG, LevelSG
from .getters import get_time_hints
from .handlers import process_result

level = Dialog(
    Window(
        Const("Подсказки"),
        Format("сейчас есть {time_hints_count}"),
        Start(Const("Добавить"), id="add_time_hint", state=TimeHintSG.time),
        state=LevelSG.time_hints,
        getter=get_time_hints,
    ),
    on_process_result=process_result,
)
