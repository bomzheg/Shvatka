from aiogram import F
from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, SwitchTo, Select, ScrollingGroup
from aiogram_dialog.widgets.text import Const, Jinja, Format

from shvatka.tgbot import states
from shvatka.tgbot.filters import is_key
from .getters import get_level_id, get_orgs, get_levels
from .handlers import (
    edit_level,
    show_level,
    level_testing,
    cancel_level_test,
    process_key_message,
    send_to_testing,
    select_level_handler,
    unlink_level_handler,
    delete_level_handler,
)

levels_list = Dialog(
    Window(
        Const("Уровни"),
        ScrollingGroup(
            Select(
                Format("{item.name_id}"),
                id="levels_select",
                items="levels",
                item_id_getter=lambda x: x.db_id,
                on_click=select_level_handler,
            ),
            id="levels_sg",
            width=1,
            height=10,
        ),
        Cancel(Const("🔙Назад")),
        state=states.LevelListSG.levels,
        getter=get_levels,
    ),
)


level_manage = Dialog(
    Window(
        Jinja("Уровень <b>{{level.name_id}}</b>\n{{rendered}}"),
        Button(
            Const("✏Редактирование"),
            id="level_edit",
            on_click=edit_level,
        ),
        Button(
            Const("📂Показать"),
            id="level_show",
            on_click=show_level,
        ),
        Button(
            Const("🧩Тестировать"),
            id="level_test",
            on_click=level_testing,
            when=F["level"].game_id,
        ),
        SwitchTo(
            Const("🧩Отправить на тестирование"),
            id="send_to_test",
            state=states.LevelManageSG.send_to_test,
            when=F["level"].game_id,
        ),
        Button(
            Const("🗑Убрать из игры"),
            id="unlink",
            on_click=unlink_level_handler,
            when=F["level"].game_id,
        ),
        Button(
            Const("🗑Удалить"),
            id="delete",
            on_click=delete_level_handler,
            when=~F["level"].game_id,
        ),
        Cancel(Const("🔙Назад")),
        state=states.LevelManageSG.menu,
        getter=get_level_id,
    ),
    Window(
        Jinja(
            "Уровень {{level.name_id}} (№{{level.number_in_game}} в игре {{game.name}})\n"
            "Кому отправить его на тестирование?\n\n"
            "ℹЧтобы добавить кого-то в этот список, нужно добавить организатора из меню игры"
        ),
        ScrollingGroup(
            Select(
                Jinja("{{item.player.name_mention}}"),
                id="game_orgs",
                item_id_getter=lambda x: x.id,
                items="orgs",
                on_click=send_to_testing,
            ),
            id="game_orgs_sg",
            width=1,
            height=10,
        ),
        SwitchTo(Const("🔙Назад"), id="back", state=states.LevelManageSG.menu),
        state=states.LevelManageSG.send_to_test,
        getter=get_orgs,
    ),
)


level_test_dialog = Dialog(
    Window(
        Jinja("Идёт тестирование уровня <b>{{level.name_id}}</b>"),
        MessageInput(func=process_key_message, content_types=ContentType.TEXT, filter=is_key),
        Button(
            Const("🔙Прервать"),
            id="level_test_cancel",
            on_click=cancel_level_test,
        ),
        getter=get_level_id,
        state=states.LevelTestSG.wait_key,
    ),
)
