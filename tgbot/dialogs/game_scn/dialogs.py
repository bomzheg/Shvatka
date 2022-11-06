from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.text import Const, Format

from tgbot.states import GameSG
from .getters import get_game_name
from .handlers import process_name

game = Dialog(
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
        state=GameSG.game_name,
    ),
    Window(
        Format("Игра <b>{game_name}</b>\n\n"),
        Const(
            "<b>Уровни<b/>\n\n"
            "Выбери уровни которые нужно добавить"
        ),
        state=GameSG.game_name,
        getter=get_game_name,
    ),
)
