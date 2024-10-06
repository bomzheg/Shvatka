from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Select,
    Button,
    Group,
    Back,
    Cancel,
    SwitchTo,
    ScrollingGroup,
    ListGroup,
)
from aiogram_dialog.widgets.text import Const, Format, Case, Jinja

from shvatka.tgbot import states
from .getters import get_available_times, get_hints
from .handlers import (
    process_time_message,
    select_time,
    process_hint,
    on_finish,
    hint_on_start,
    hint_edit_on_start,
    process_edit_time_message,
    edit_single_hint,
    save_edited_time_hint,
    delete_single_hint,
)
from shvatka.tgbot.dialogs.preview_data import TIMES_PRESET, PreviewSwitchTo

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
        preview_add_transitions=[PreviewSwitchTo(state=states.TimeHintSG.hint)],
    ),
    Window(
        Jinja("Подсказка выходящая в {{time}} мин."),
        Case(
            {
                False: Const("Присылай сообщения с подсказками (текст, фото, видео итд)"),
                True: Jinja(
                    "{{hints | hints}}\n"
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
        preview_data={"has_hints": True},
    ),
    on_start=hint_on_start,
)


time_hint_edit = Dialog(
    Window(
        Jinja("Подсказка выходящая в {{time}}:" "{{hints | hints}}"),
        SwitchTo(
            Const("Изменить время"),
            id="change_time",
            state=states.TimeHintEditSG.time,
        ),
        ScrollingGroup(
            ListGroup(
                Button(
                    Jinja("{{item[1] | single_hint}}"),
                    on_click=edit_single_hint,
                    id="show",
                ),
                Button(
                    Const("🗑"),
                    on_click=delete_single_hint,
                    id="delete",
                ),
                id="hints",
                item_id_getter=lambda x: x[0],
                items="numerated_hints",
            ),
            id="hints_sg",
            width=2,
            height=10,
        ),
        Button(
            text=Const("Сохранить изменения"),
            id="save_time_hint",
            on_click=save_edited_time_hint,
        ),
        Cancel(text=Const("Вернуться, ничего не менять")),
        getter=get_hints,
        state=states.TimeHintEditSG.details,
    ),
    Window(
        Jinja("Введи новое время выхода подсказки"),
        MessageInput(func=process_edit_time_message),
        getter=get_hints,
        state=states.TimeHintEditSG.time,
    ),
    on_start=hint_edit_on_start,
)
