from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    ScrollingGroup,
    Select,
    SwitchTo,
    Group,
    ListGroup,
)
from aiogram_dialog.widgets.text import Const, Jinja, Format

from shvatka.tgbot import states
from .getters import (
    get_timers,
    get_timer,
)
from .handlers import (
    on_start_timers,
    save_timers,
    process_timers_result,
    start_edit_timer,
    on_start_timer,
    start_new_timer,
    process_incorrect_time_message,
    process_correct_time_message,
    select_time,
    start_effects,
    on_process_timer_result,
    save_timer,
    delete_timer,
)
from shvatka.tgbot.dialogs.time_hint.getters import get_available_times

timers_dialog = Dialog(
    Window(
        Jinja(
            "Уровень <b>{{level_id}}</b>\n\n"
            "🕑Таймеры: {{timers | length}}\n"
            "{% for timer in timers %}"
            "{{ timer.action_time }}: {{ timer.effects | effects }}\n"
            "{% endfor %}"
        ),
        ScrollingGroup(
            ListGroup(
                Button(
                    Jinja("{{item.action_time}}: {{item.effects | effects}}"),
                    id="edit_timer",
                    on_click=start_edit_timer,
                ),
                Button(
                    Const("🗑"),
                    id="delete_timer",
                    on_click=delete_timer,
                ),
                id="timer_conditions",
                item_id_getter=lambda x: x.action_time,
                items="timers",
            ),
            id="timer_conditions_sg",
            width=2,
            height=10,
        ),
        Button(id="add_timer_start", text=Const("➕Добавить"), on_click=start_new_timer),
        Button(
            Const("✅Готово"),
            id="save",
            on_click=save_timers,
        ),
        Cancel(Const("🔙Назад")),
        getter=get_timers,
        state=states.LevelTimersSG.menu,
    ),
    on_process_result=process_timers_result,
    on_start=on_start_timers,
)

timer_dialog = Dialog(
    Window(
        Jinja("{{time}}: {{effects | effects}}"),
        SwitchTo(
            Jinja("🕑Время"),
            id="to_timer",
            state=states.LevelTimerSG.timer,
        ),
        Button(
            id="to_effects",
            text=Jinja("✨Эффекты"),
            on_click=start_effects,
        ),
        Button(
            id="save_timer",
            text=Jinja("✅Готово"),
            when=F["time"] & F["effects"].id,
            on_click=save_timer,
        ),
        Cancel(text=Const("🔙Вернуться, не сохранять")),
        state=states.LevelTimerSG.menu,
        getter=get_timer,
    ),
    Window(
        Const("Время выхода подсказки (можно выбрать или ввести)"),
        TextInput(
            id="time",
            type_factory=int,
            on_success=process_correct_time_message,
            on_error=process_incorrect_time_message,
        ),
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
        SwitchTo(
            id="back",
            state=states.LevelTimerSG.menu,
            text=Jinja("🔙Готово"),
        ),
        Cancel(text=Const("🔙Вернуться, не сохранять")),
        state=states.LevelTimerSG.timer,
        getter=get_available_times,
    ),
    on_process_result=on_process_timer_result,
    on_start=on_start_timer,
)
