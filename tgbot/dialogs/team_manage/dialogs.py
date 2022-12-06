from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import SwitchTo, Cancel
from aiogram_dialog.widgets.text import Const, Jinja

from tgbot import states
from .getters import get_my_team_
from .handlers import rename_team_handler, change_desc_team_handler

captains_bridge = Dialog(
    Window(
        Jinja(
            "Капитанский мостик.\n"
            "🚩Команда: <b>{{team.name}}</b>\n"
            "{% if team.description %}"
            "📃Девиз: {{team.description}}\n"
            "{% endif %}"
            "{% if team.captain %}"
            "👑Капитан: {{team.captain.user.name_mention}}\n"
            "{% endif %}"
        ),
        Cancel(Const("⤴Назад")),
        SwitchTo(Const("✍️Переименовать"), id="rename", state=states.CaptainsBridgeSG.name),
        SwitchTo(Const("📃Изменить девиз"), id="change_desc", state=states.CaptainsBridgeSG.description),
        state=states.CaptainsBridgeSG.main,
        getter=get_my_team_,
    ),
    Window(
        Jinja("Переименовать команду 🚩<b>{{team.name}}</b>"),
        SwitchTo(Const("⤴Назад"), id="back", state=states.CaptainsBridgeSG.main),
        TextInput(id="rename", on_success=rename_team_handler),
        getter=get_my_team_,
        state=states.CaptainsBridgeSG.name,
    ),
    Window(
        Jinja("Изменить девиз команды 🚩<b>{{team.name}}</b>"),
        SwitchTo(Const("⤴Назад"), id="back", state=states.CaptainsBridgeSG.main),
        TextInput(id="change_desc", on_success=change_desc_team_handler),
        getter=get_my_team_,
        state=states.CaptainsBridgeSG.description,
    ),
)
