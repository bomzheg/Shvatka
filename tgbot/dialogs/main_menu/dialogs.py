from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Start
from aiogram_dialog.widgets.text import Const, Format

from tgbot.states import MyGamesPanel, MainMenu
from .getters import get_player

main_menu = Dialog(
    Window(
        Format("Главное меню"),
        Cancel(Const("❌Закрыть")),
        Start(Const("🗄Мои игры"), id="my_games", state=MyGamesPanel.choose_game),
        # прошедшие игры
        # ачивки
        # уровни (не привязанные к играм?)
        # promote
        state=MainMenu.main,
        getter=get_player,
    ),
)
