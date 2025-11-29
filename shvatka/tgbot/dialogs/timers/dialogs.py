from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
)
from aiogram_dialog.widgets.text import Const, Jinja

from shvatka.tgbot import states
from .getters import (
    get_timers,
)
from .handlers import (
    on_start_timers,
    save_timers,
    process_timers_result,
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
