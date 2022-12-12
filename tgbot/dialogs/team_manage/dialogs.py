from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import SwitchTo, Cancel, ScrollingGroup, Select, Button
from aiogram_dialog.widgets.text import Const, Jinja, Format

from tgbot import states
from .getters import get_my_team_, get_team_with_players, get_selected_player
from .handlers import rename_team_handler, change_desc_team_handler, select_player, change_permission_handler

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
        SwitchTo(Const("👥Игроки"), id="players", state=states.CaptainsBridgeSG.players),
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
    Window(
        Jinja("Игроки команды 🚩<b>{{team.name}}</b>"),
        SwitchTo(Const("⤴Назад"), id="back", state=states.CaptainsBridgeSG.main),
        ScrollingGroup(
            Select(
                Jinja("{{item.player.user.name_mention}}"),
                id="players",
                item_id_getter=lambda x: x.player.id,
                items="players",
                on_click=select_player,
            ),
            id="players_sg",
            width=1,
            height=10,
        ),
        getter=get_team_with_players,
        state=states.CaptainsBridgeSG.players,
    ),
    Window(
        Jinja(
            "Меню игрока {{selected_player.user.name_mention}} команды 🚩{{team.name}}"
        ),
        SwitchTo(Const("⤴В меню команды"), id="back", state=states.CaptainsBridgeSG.main),
        SwitchTo(Const("⤴Назад"), id="back", state=states.CaptainsBridgeSG.players),
        Button(
            Format("{can_manage_waivers}Подавать вейверы"),
            id="can_manage_waivers",
            on_click=change_permission_handler,
        ),
        Button(
            Format("{can_manage_players}Управлять игроками"),
            id="can_manage_players",
            on_click=change_permission_handler,
        ),
        Button(
            Format("{can_change_team_name}Переименовывать команду"),
            id="can_change_team_name",
            on_click=change_permission_handler,
        ),
        Button(
            Format("{can_add_players}Добавлять игроков"),
            id="can_add_players",
            on_click=change_permission_handler,
        ),
        Button(
            Format("{can_remove_players}Удалять игроков"),
            id="can_remove_players",
            on_click=change_permission_handler,
        ),
        getter=(get_my_team_, get_selected_player),
        state=states.CaptainsBridgeSG.player,
    )
)
