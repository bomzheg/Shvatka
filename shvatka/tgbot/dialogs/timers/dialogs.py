from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    ScrollingGroup,
    Select,
    Start,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Jinja

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
    on_start_timer, start_new_timer,
)


timers_dialog = Dialog(
    Window(
        Jinja(
            "Уровень <b>{{level_id}}</b>\n\n"
            "🕑Таймеры: {{timers | length}}\n"
            "{% for timer in timers %}"
            "{{timer.action_time}}: {{timer.effects | effects}}"
            "{% endfor %}"
        ),
        ScrollingGroup(
            Select(
                Jinja("{{timer.action_time}}: {{timer.effects | effects}}"),
                id="timer_conditions",
                item_id_getter=lambda x: x.action_time,
                items="timers",
                on_click=start_edit_timer,
            ),
            id="timer_conditions_sg",
            width=1,
            height=10,
        ),
        Button(
            id="add_timer_start",
            text=Const("➕Добавить"),
            on_click=start_new_timer
        ),
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
            Jinja("Время"),
            id="to_timer",
            state=states.LevelTimerSG.timer,
        ),
        state=states.LevelTimerSG.menu,
        getter=get_timer,
    ),
    Window(
        Jinja("таймер"),
        state=states.LevelTimerSG.timer,
    ),
    on_start=on_start_timer,
)
