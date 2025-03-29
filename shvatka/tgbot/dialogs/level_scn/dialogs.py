from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, ScrollingGroup, Select, Next, SwitchTo
from aiogram_dialog.widgets.text import Const, Jinja

from shvatka.tgbot import states
from .getters import (
    get_time_hints,
    get_level_id,
    get_level_data,
    get_keys,
    get_bonus_keys,
    get_sly_keys,
    get_bonus_hint_conditions,
)
from .handlers import (
    process_time_hint_result,
    start_add_time_hint,
    process_id,
    save_level,
    save_hints,
    process_level_result,
    start_keys,
    start_hints,
    not_correct_id,
    check_level_id,
    on_start_level_edit,
    on_start_hints_edit,
    convert_keys,
    on_correct_keys,
    not_correct_keys,
    clear_hints,
    convert_bonus_keys,
    on_correct_bonus_keys,
    not_correct_bonus_keys,
    start_sly_keys,
    start_edit_time_hint,
    on_start_sly_keys,
    save_sly_keys,
)
from shvatka.tgbot.dialogs.preview_data import PreviewStart

level = Dialog(
    Window(
        Const(
            "<b>ID уровня</b>\n\n"
            "Для начала дай уровню короткое описание (ID) (цифры, латинские буквы). "
            "Оно будет использовано в дальнейшем при создании игры, "
            "для указания очередности уровней.\n"
            "\n"
            "Внимание! ID и название файла не должны содержать "
            "конфиденциальной информации, дающих представление о "
            "ключах, локациях и другой существенной информации "
            "поскольку ID и название файла попадают в лог-файлы, предназначенные "
            "для чтения системным администратором"
        ),
        TextInput(
            type_factory=check_level_id,
            on_error=not_correct_id,
            on_success=process_id,
            id="level_id",
        ),
        state=states.LevelSG.level_id,
        preview_add_transitions=[Next()],
    ),
    Window(
        Jinja(
            "Написание уровня {{level_id}}:\n"
            "{% if keys %}"
            "🔑Ключей: {{ keys | length }}\n"
            "{% else %}"
            "🔑Ключи не введены\n"
            "{% endif %}"
            "{% if sly_types %}"
            "🗝Разновидностей хитрых ключей: {{sly_types}}\n"
            "{% endif %}"
            "\n💡Подсказки:\n"
            "{% if time_hints %}"
            "{{time_hints | time_hints}}"
            "{% else %}"
            "пока нет ни одной"
            "{% endif %}"
        ),
        Button(Const("🔑Ключи"), id="keys", on_click=start_keys),
        Button(Const("🗝Хитрые ключи"), id="sly_keys", on_click=start_sly_keys, when=F["keys"]),
        Button(Const("💡Подсказки"), id="hints", on_click=start_hints),
        Button(
            Const("✅Готово, сохранить"),
            id="save",
            on_click=save_level,
            when=F["keys"] & F["time_hints"],
        ),
        state=states.LevelSG.menu,
        getter=get_level_data,
        preview_data={
            "level_id": "Pinky Pie",
        },
        preview_add_transitions=[
            PreviewStart(state=states.LevelKeysSG.keys),
            PreviewStart(state=states.LevelSlyKeysSg.menu),
            PreviewStart(state=states.LevelHintsSG.time_hints),
            Cancel(),
        ],
    ),
    on_process_result=process_level_result,
)

level_edit_dialog = Dialog(
    Window(
        Jinja(
            "Редактирование уровня {{level_id}}:\n"
            "{% if keys %}"
            "🔑Ключей: {{ keys | length }}\n"
            "{% else %}"
            "🔑Ключи не введены\n"
            "{% endif %}"
            "{% if sly_types %}"
            "🗝Разновидностей хитрых ключей: {{sly_types}}\n"
            "{% endif %}"
            "\n💡Подсказки:\n"
            "{% if time_hints %}"
            "{{time_hints | time_hints}}"
            "{% else %}"
            "пока нет ни одной"
            "{% endif %}"
        ),
        Button(Const("🔑Ключи"), id="keys", on_click=start_keys),
        Button(Const("🗝Хитрые ключи"), id="sly_keys", on_click=start_sly_keys, when=F["keys"]),
        Button(Const("💡Подсказки"), id="hints", on_click=start_hints),
        Button(
            Const("💾Готово, сохранить"),
            id="save",
            on_click=save_level,
            when=F["keys"] & F["time_hints"],
        ),
        Cancel(Const("🔙Назад")),
        state=states.LevelEditSg.menu,
        getter=get_level_data,
        preview_data={
            "level_id": "Pinky Pie",
        },
        preview_add_transitions=[
            PreviewStart(state=states.LevelKeysSG.keys),
            PreviewStart(state=states.LevelSlyKeysSg.menu),
            PreviewStart(state=states.LevelHintsSG.time_hints),
        ],
    ),
    on_process_result=process_level_result,
    on_start=on_start_level_edit,
)

keys_dialog = Dialog(
    Window(
        Jinja("Уровень <b>{{level_id}}</b>\n\n"),
        Const("🔑<b>Ключи уровня</b>\n"),
        Jinja(
            "Сейчас сохранены ключи:\n"
            "{% for key in keys %}"
            "🔑<code>{{key}}</code>\n"
            "{% endfor %}"
            "\n Для изменения пришли сообщение с новыми ключами в формате: ",
            when=F["keys"],
        ),
        Const(
            "Отлично, перейдём к ключам. Ключи принимаются в следующих форматах: ", when=~F["keys"]
        ),
        Const(
            "<code>SHСЛОВО СХСЛОВО</code>.\n"
            "Если требуется указать несколько ключей напишите каждый с новой строки, например:\n"
            "<pre>"
            "СХСЛОВО1\n"
            "СХСЛОВО2\n"
            "СХСЛОВО3\n"
            "</pre>"
        ),
        Cancel(Const("🔙Назад")),
        TextInput(
            type_factory=convert_keys,
            on_success=on_correct_keys,
            on_error=not_correct_keys,
            id="keys_input",
        ),
        state=states.LevelKeysSG.keys,
        getter=(get_level_id, get_keys),
    ),
)

hints_dialog = Dialog(
    Window(
        Jinja("💡Подсказки уровня {{level_id}}:\n"),
        Jinja(
            "{% if time_hints %}"
            "{{time_hints | time_hints}}"
            "{% else %}"
            "пока нет ни одной"
            "{% endif %}"
        ),
        ScrollingGroup(
            Select(
                Jinja("{{item | time_hint}}"),
                id="level_hints",
                item_id_getter=lambda x: x.time,
                items="time_hints",
                on_click=start_edit_time_hint,
            ),
            id="level_hints_sg",
            width=1,
            height=10,
        ),
        Button(Const("➕Добавить подсказку"), id="add_time_hint", on_click=start_add_time_hint),
        Button(
            Const("✅Готово"),
            id="save",
            on_click=save_hints,
            when=F["dialog_data"]["time_hints"].len() > 1,
        ),
        Button(
            Const("🗑Очистить подсказки"),
            id="clear",
            on_click=clear_hints,
            when=F["dialog_data"]["time_hints"].len() > 0,
        ),
        Cancel(Const("🔙Назад")),
        state=states.LevelHintsSG.time_hints,
        getter=get_time_hints,
        preview_data={
            "time_hints": [],
            "level_id": "Pinky Pie",
        },
        preview_add_transitions=[
            PreviewStart(state=states.TimeHintSG.time),
            PreviewStart(state=states.TimeHintEditSG.details),
        ],
    ),
    on_process_result=process_time_hint_result,
    on_start=on_start_hints_edit,
)

sly_keys_dialog = Dialog(
    Window(
        Jinja(
            "Уровень <b>{{level_id}}</b>\n\n"
            "Бонусных ключей: {{bonus_keys | length}}\n"
            "Ключей с бонусными подсказками: {{bonus_hint_conditions | length}}\n"
            "Нелинейных ключей: {{routed_conditions | length}}\n"
        ),
        SwitchTo(
            Const("Бонусные ключи"),
            id="to_bonus_keys",
            state=states.LevelSlyKeysSg.bonus_keys,
        ),
        SwitchTo(
            Const("Ключи с бонусными подсказками"),
            id="to_bonus_hunt_keys",
            state=states.LevelSlyKeysSg.bonus_hint_keys,
        ),
        SwitchTo(
            Const("Нелинейные ключи"),
            id="to_routed_keys",
            state=states.LevelSlyKeysSg.routed_keys,
            when=F["game_id"],
        ),
        Button(
            Const("✅Готово"),
            id="save",
            on_click=save_sly_keys,
        ),
        Cancel(Const("🔙Назад")),
        getter=get_sly_keys,
        state=states.LevelSlyKeysSg.menu,
    ),
    Window(
        Jinja("Уровень <b>{{level_id}}</b>\n\n"),
        Const("💰<b>Бонусные ключи уровня</b>\n"),
        Jinja(
            "Сейчас сохранены бонусные ключи:\n"
            "{% for key in bonus_keys %}"
            "💰<code>{{key.text}}</code>: {{key.bonus_minutes}} мин.\n"
            "{% endfor %}"
            "\n Для изменения пришли сообщение с новыми бонусными ключами в формате: ",
            when=F["bonus_keys"],
        ),
        Const(
            "У данного уровня нет бонусных ключей. Ключи принимаются в следующих форматах: ",
            when=~F["bonus_keys"],
        ),
        Const(
            "<code>СХБОНУСНЫЙ</code> 2\n"
            "<code>СХШТРАФНОЙ</code> -3\n"
            "<code>СХДРУГОЙБОНУСНЫЙ</code> 5\n"
        ),
        SwitchTo(Const("🔙Назад"), id="to_menu", state=states.LevelSlyKeysSg.menu),
        TextInput(
            type_factory=convert_bonus_keys,
            on_success=on_correct_bonus_keys,
            on_error=not_correct_bonus_keys,
            id="keys_input",
        ),
        getter=(get_level_id, get_bonus_keys),
        state=states.LevelSlyKeysSg.bonus_keys,
    ),
    Window(
        Jinja("Уровень <b>{{level_id}}</b>\n\n"),
        Jinja(
            "Текущие ключи бонусных подсказок:\n"
            "{% for index, c in bonus_hint_conditions.items() %}"
            "{{index + 1}}{{c.bonus_hint | hints}}"
            "{% for key in c.keys %}"
            "🔑<code>{{key}}</code>\n"
            "{% endfor %}"
            "{% endfor %}",
            when=F["bonus_hint_conditions"],
        ),
        Select(
            Jinja("{{item}} - {{bonus_hint_conditions[item].bonus_hint | hints}}"),
            id="bonus_hint_conditions",
            item_id_getter=lambda x: x,
            items="bonus_hint_conditions",
            # on_click=,  ## TODO
        ),
        SwitchTo(Const("🔙Назад"), id="to_menu", state=states.LevelSlyKeysSg.menu),
        getter=(get_level_id, get_bonus_hint_conditions),
        state=states.LevelSlyKeysSg.bonus_hint_keys,
    ),
    Window(
        Jinja("Уровень <b>{{level_id}}</b>\n\n"),
        Jinja(
            "Текущие нелинейные ключи:\n"
            "{% for c in routed_conditions %}"
            "🗝🗝🗝 -> {{c.next_level}}:"
            "{% for key in c.keys: %}"
            "🔑<code>{{key}}</code>\n"
            "{% endfor %}"
            "{% endfor %}",
            when=F["routed_conditions"],
        ),
        SwitchTo(Const("🔙Назад"), id="to_menu", state=states.LevelSlyKeysSg.menu),
        getter=(get_level_id, get_sly_keys),
        state=states.LevelSlyKeysSg.routed_keys,
    ),
    on_start=on_start_sly_keys,
)
