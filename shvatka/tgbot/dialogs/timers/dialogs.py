from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    Group,
    ListGroup,
    ScrollingGroup,
    Select,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Format, Jinja

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.preview_data import (
    PREVIEW_EFFECTS,
    PREVIEW_LEVEL,
    PREVIEW_TIMER,
    PREVIEW_TIMERS,
    TIMES_PRESET,
    PreviewStart,
)
from shvatka.tgbot.dialogs.time_hint.getters import get_available_times

from .getters import (
    get_timer,
    get_timers,
)
from .handlers import (
    delete_timer,
    on_process_timer_result,
    on_start_timer,
    on_start_timers,
    process_correct_time_message,
    process_incorrect_time_message,
    process_timers_result,
    save_timer,
    save_timers,
    select_time,
    start_edit_timer,
    start_effects,
    start_new_timer,
)

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
        preview_data={
            "level_id": PREVIEW_LEVEL.name_id,
            "timers": PREVIEW_TIMERS,
        },
        preview_add_transitions=[PreviewStart(states.LevelTimerSG.menu)],
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
        preview_data={
            "time": PREVIEW_TIMER.action_time,
            "effects": PREVIEW_EFFECTS,
        },
        preview_add_transitions=[PreviewStart(states.EffectsSG.menu)],
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
        preview_data={"times": TIMES_PRESET},
    ),
    on_process_result=on_process_timer_result,
    on_start=on_start_timer,
)
