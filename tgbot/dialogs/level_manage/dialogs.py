from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel
from aiogram_dialog.widgets.text import Const, Jinja

from tgbot.filters import is_key
from tgbot.states import LevelManageSG, LevelTest
from .getters import get_level_id
from .handlers import edit_level, show_level, level_testing, cancel_level_test, process_key_message

level_manage = Dialog(
    Window(
        Jinja("Уровень <b>{{level.name_id}}</b>"),
        Cancel(Const("⤴Назад")),
        Button(
            Const("✏Редактирование"),
            id="level_edit",
            on_click=edit_level,
            when="False",
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
        ),
        state=LevelManageSG.menu,
        getter=get_level_id,
    ),
)


level_test_dialog = Dialog(
    Window(
        Jinja("Идёт тестирование уровня <b>{{level.name_id}}</b>"),
        Button(
            Const("⤴Назад"),
            id="level_test_cancel",
            on_click=cancel_level_test,
        ),
        MessageInput(
            func=process_key_message,
            content_types=ContentType.TEXT,
            filter=is_key
        ),
        getter=get_level_id,
        state=LevelTest.wait_key,
    ),
)
