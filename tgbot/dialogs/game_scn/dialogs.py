from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import ScrollingGroup, Multiselect, Button, Select, Cancel
from aiogram_dialog.widgets.text import Const, Format

from tgbot.states import GameWriteSG, GameEditSG
from .getters import get_game_name, select_my_levels, select_full_game
from .handlers import process_name, save_game, edit_level, add_level

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
        MessageInput(func=process_name),
        state=GameWriteSG.game_name,
    ),
    Window(
        Format("Игра <b>{game_name}</b>\n\n"),
        Const(
            "<b>Уровни</b>\n\n"
            "Выбери уровни которые нужно добавить"
        ),
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
        state=GameWriteSG.levels,
        getter=[get_game_name, select_my_levels],
    ),
)


game_editor = Dialog(
    Window(
        Format("Игра <b>{game.name}</b>\n\n"),
        Const("<b>Уровни игры</b>"),
        Cancel(Const("⤴Назад")),
        Button(Const("📑Добавить уровень"), id="add_level", on_click=add_level),
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
        state=GameEditSG.current_levels,
        getter=select_full_game,
    ),
)
