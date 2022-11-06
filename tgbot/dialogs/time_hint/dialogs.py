from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Select, Button, Group
from aiogram_dialog.widgets.text import Const, Format, Case

from tgbot.states import TimeHintSG
from .getters import get_available_times, get_hints
from .handlers import process_time_message, select_time, process_hint, on_finish

time_hint = Dialog(
    Window(
        Const("Время выхода подсказки (можно выбрать или ввести)"),
        #  TODO can set only time greater that before hint
        MessageInput(func=process_time_message),
        Group(
            Select(
                Format("{item}"),
                id="hint_times",
                item_id_getter=lambda x: x,
                items="times",
                on_click=select_time,
            ),
            id="times_group",
            width=3,
        ),
        state=TimeHintSG.time,
        getter=get_available_times,
    ),
    Window(
        Case(
            {
                False: Const("Присылай сообщения с подсказками (текст, фото, видео итд)"),
                True: Format(
                    "я сохранил {hints_count} сообщения с подсказками. "
                    "Можно прислать ещё сообщения или перейти к следующей подсказке"
                ),
            },
            selector="has_hints",
        ),
        MessageInput(func=process_hint),
        Button(
            Const("К следующей подсказке"),
            id="to_next_hint",
            when=lambda data, *args: data["has_hints"],
            on_click=on_finish,
        ),
        getter=get_hints,
        state=TimeHintSG.hint,
    ),
)
