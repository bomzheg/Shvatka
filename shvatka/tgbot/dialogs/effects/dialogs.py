from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Jinja

from shvatka.tgbot import states
from .getters import get_effects
from .handlers import (
    process_level_up_change,
    effects_on_start,
    save_effects,
)


effects = Dialog(
    Window(
        Jinja(
            "Редактирование эффектов:\n"
            "{% if hints %}"
            "Подсказки: {{hints | hints}}\n"
            "{% endif %}"
            "{% if bonus_minutes %}"
            "{% if bonus_minutes > 0 %}"
            "Бонус"
            "{% elif bonus_minutes < 0 %}"
            "Штраф"
            "{% endif %}: {{bonus_minutes}} минут\n"
            "{% endif %}"
            "{% if level_up %}"
            "{% if routed_level_up %}"
            "Переход на уровень {{routed_level_up}}"
            "{% else %}"
            "Переход на следующий уровень"
            "{% endif %}"
            "{% endif %}"
        ),
        SwitchTo(
            Jinja("Подсказки"),
            id="to_hints",
            state=states.EffectsSG.hints,
        ),
        SwitchTo(
            Jinja("Бонус"),
            id="to_bonus",
            state=states.EffectsSG.bonus,
        ),
        SwitchTo(
            Jinja("Переход на уровень"),
            id="to_routed",
            state=states.EffectsSG.routed_level_up,
        ),
        Button(Jinja("Завершение уровня"), id="level_up", on_click=process_level_up_change),
        Button(
            Jinja("Сохранить"),
            id="done",
            on_click=save_effects,
        ),
        Cancel(),
        state=states.EffectsSG.menu,
        getter=get_effects,
    ),
    Window(
        Jinja("подсказки"),
        SwitchTo(
            Jinja("К меню эффектов"),
            id="to_menu",
            state=states.EffectsSG.menu,
        ),
        state=states.EffectsSG.hints,
    ),
    Window(
        Jinja("Бонус"),
        SwitchTo(
            Jinja("К меню эффектов"),
            id="to_menu",
            state=states.EffectsSG.menu,
        ),
        state=states.EffectsSG.bonus,
    ),
    Window(
        Jinja("роутед"),
        SwitchTo(
            Jinja("К меню эффектов"),
            id="to_menu",
            state=states.EffectsSG.menu,
        ),
        state=states.EffectsSG.routed_level_up,
    ),
    on_start=effects_on_start,
)
