from aiogram import F
from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    ScrollingGroup,
    Multiselect,
    Button,
    Select,
    Cancel,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Format, Jinja

from shvatka.tgbot import states
from .getters import get_game_name, select_my_levels, select_full_game
from .handlers import process_name, save_game, edit_level, add_level_handler, process_zip_scn

game_writer = Dialog(
    Window(
        Const(
            "<b>Выбираем название игры</b>\n\n"
            "Для этого дай ей название."
            "Название игры будет видно всем схватчикам во время игры "
            "и в последующих статистиках, поэтому выбирай мудро!"
            "\n"
            "Внимание! ID и название файла не должны содержать "
            "конфиденциальной информации, дающих представление о "
            "ключах, локациях и другой существенной информации "
            "поскольку ID и название файла попадают в лог-файлы, предназначенные "
            "для чтения системным администратором"
        ),
        Cancel(Const("🔙Отменить")),
        MessageInput(func=process_name),
        SwitchTo(Const("Загрузить из zip"), id="game_from_zip", state=states.GameWriteSG.from_zip),
        state=states.GameWriteSG.game_name,
    ),
    Window(
        Jinja("Игра <b>{{game_name}}</b>\n\n"),
        Const("<b>Уровни</b>\n\n" "Выбери уровни которые нужно добавить"),
        Cancel(Const("🔙Не создавать игру")),
        ScrollingGroup(
            Multiselect(
                Format("✓ {item.name_id}"),
                Format("{item.name_id}"),
                id="my_free_level_ids",
                item_id_getter=lambda x: x.db_id,
                items="levels",
            ),
            id="my_free_levels_sg",
            width=1,
            height=10,
        ),
        Button(
            Const("Сохранить"),
            id="save_levels",
            on_click=save_game,
        ),
        state=states.GameWriteSG.levels,
        getter=[get_game_name, select_my_levels],
    ),
    Window(
        Const("Жду zip-файл с готовой игрой"),
        Cancel(Const("🔙Отменить")),
        MessageInput(func=process_zip_scn, filter=F.content_type == ContentType.DOCUMENT),
        state=states.GameWriteSG.from_zip,
    ),
)


game_editor = Dialog(
    Window(
        Jinja("Игра <b>{{game.name}}</b>\n\n"),
        Const("<b>Уровни игры</b>"),
        Cancel(Const("🔙Назад")),
        SwitchTo(
            Const("📑Добавить уровень"),
            id="to_add_level",
            state=states.GameEditSG.add_level,
        ),
        ScrollingGroup(
            Select(
                Format("{item.name_id}"),
                id="game_level_ids",
                item_id_getter=lambda x: x.db_id,
                items="levels",
                on_click=edit_level,
            ),
            id="game_levels_sg",
            width=1,
            height=10,
        ),
        state=states.GameEditSG.current_levels,
        getter=select_full_game,
    ),
    Window(
        Jinja("Игра <b>{{game.name}}</b>\n\n"),
        Const("<b>Уровни</b>\n\n" "Выбери уровни которые нужно добавить"),
        SwitchTo(Const("🔙Назад"), id="back", state=states.GameEditSG.current_levels),
        ScrollingGroup(
            Select(
                Format("{item.name_id}"),
                id="level_select",
                item_id_getter=lambda x: x.db_id,
                items="levels",
                on_click=add_level_handler,
            ),
            id="my_free_levels_sg",
            width=1,
            height=10,
        ),
        state=states.GameEditSG.add_level,
        getter=(select_full_game, select_my_levels),
    ),
)
