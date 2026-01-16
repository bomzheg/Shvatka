from PIL.ImageShow import show
from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    SwitchTo, ScrollingGroup, ListGroup,
)
from aiogram_dialog.widgets.text import Jinja, Const, Case

from shvatka.tgbot import states
from .getters import get_effects, get_hints
from .handlers import (
    process_level_up_change,
    effects_on_start,
    save_effects, show_single_hint, delete_single_hint, process_hint,
)


effects = Dialog(
    Window(
        Jinja(
            "<pre>{{dialog_data['effect_id']}}</pre>\n"
            "Эффекты:\n"
            "{% if hints %}"
            "💡Подсказки: {{hints | hints}}\n"
            "{% endif %}"
            "{% if bonus_minutes %}"
            "{% if bonus_minutes > 0 %}"
            "💰Бонус"
            "{% elif bonus_minutes < 0 %}"
            "💸Штраф"
            "{% endif %}: {{bonus_minutes}} минут\n"
            "{% endif %}"
            "{% if level_up %}"
            "{% if next_level %}"
            "🔀Переход на уровень {{next_level}}"
            "{% else %}"
            "🚩Переход на следующий уровень"
            "{% endif %}"
            "{% endif %}"
        ),
        SwitchTo(
            Jinja("💡Подсказки"),
            id="to_hints",
            state=states.EffectsSG.hints,
        ),
        SwitchTo(
            Jinja("💰Бонус"),
            id="to_bonus",
            state=states.EffectsSG.bonus,
        ),
        Button(Jinja("🚩Завершение уровня"), id="level_up", on_click=process_level_up_change),
        SwitchTo(
            Jinja("🔀Переход на уровень"),
            id="to_routed",
            state=states.EffectsSG.routed_level_up,
            when=F["level_up"],
        ),
        Button(
            Jinja("✅Сохранить"),
            id="done",
            on_click=save_effects,
        ),
        Cancel(Const("🔙Назад")),
        state=states.EffectsSG.menu,
        getter=get_effects,
    ),
    Window(
        Jinja("💰Бонус"),
        SwitchTo(
            Jinja("🔙К меню эффектов"),
            id="to_menu",
            state=states.EffectsSG.menu,
        ),
        state=states.EffectsSG.bonus,
    ),
    Window(
        Jinja("🔀Переход на уровень"),
        SwitchTo(
            Jinja("🔙К меню эффектов"),
            id="to_menu",
            state=states.EffectsSG.menu,
        ),
        state=states.EffectsSG.routed_level_up,
    ),
    Window(
        Jinja(
            "💡Подсказки\n\n"
            "{{hints | hints}}"
        ),
        ScrollingGroup(
            ListGroup(
                Button(
                    Jinja("{{item[1] | single_hint}}"),
                    on_click=show_single_hint,
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
        SwitchTo(Const("📝Добавить"), state=states.EffectsSG.add_hints, id="to_add_part"),
        SwitchTo(
            Jinja("🔙К меню эффектов"),
            id="to_menu",
            state=states.EffectsSG.menu,
        ),
        getter=get_hints,
        state=states.EffectsSG.hints,
    ),
    Window(
        Jinja("Подсказка выходящая в {{time}} мин."),
        Case(
            {
                False: Const("Присылай сообщения с подсказками (текст, фото, видео итд)"),
                True: Jinja("{{hints | hints}}\n" "Можно прислать ещё сообщения или вернуться"),
            },
            selector=F["hints"].len() > 0,
        ),
        MessageInput(func=process_hint),
        SwitchTo(
            text=Const("Вернуться"),
            state=states.EffectsSG.hints,
            id="to_details",
        ),
        getter=get_hints,
        state=states.EffectsSG.add_hints,
    ),
    on_start=effects_on_start,
)
