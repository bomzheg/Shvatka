from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Select, Button, Group, Back, Cancel
from aiogram_dialog.widgets.text import Const, Format, Case, Jinja

from shvatka.tgbot import states
from .getters import get_available_times, get_hints
from .handlers import process_time_message, select_time, process_hint, on_finish, hint_on_start
from shvatka.tgbot.dialogs.preview_data import TIMES_PRESET

time_hint = Dialog(
    Window(
        Const("Время выхода подсказки (можно выбрать или ввести)"),
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
        Cancel(text=Const("Вернуться, не нужна подсказка")),
        state=states.TimeHintSG.time,
        getter=get_available_times,
        preview_data={"times": TIMES_PRESET},
    ),
    Window(
        Jinja("Подсказка выходящая в {{time}} мин."),
        Case(
            {
                False: Const("Присылай сообщения с подсказками (текст, фото, видео итд)"),
                True: Jinja(
                    "{{rendered}}\n"
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
        Back(text=Const("Изменить время")),
        getter=get_hints,
        state=states.TimeHintSG.hint,
        preview_data={"has_hints": True, "rendered": "📃🪪"},
    ),
    on_start=hint_on_start,
)
