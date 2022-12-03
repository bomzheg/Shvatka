from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import SwitchTo, Cancel
from aiogram_dialog.widgets.text import Const, Jinja

from tgbot.states import CaptainsBridgeSG
from .getters import get_my_team_
from .handlers import rename_team_handler

captains_bridge = Dialog(
    Window(
        Jinja("Капитанский мостик команды <b>{{team.name}}</b>"),
        Cancel(Const("⤴Назад")),
        SwitchTo(Const("Переименовать"), id="rename", state=CaptainsBridgeSG.name),
        state=CaptainsBridgeSG.main,
        getter=get_my_team_,
    ),
    Window(
        Jinja("Переименовать команду <b>{{team.name}}</b>"),
        SwitchTo(Const("⤴Назад"), id="back", state=CaptainsBridgeSG.main),
        TextInput(id="rename", on_success=rename_team_handler),
        getter=get_my_team_,
        state=CaptainsBridgeSG.name,
    ),
)
