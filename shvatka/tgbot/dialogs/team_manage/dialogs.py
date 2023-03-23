from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import SwitchTo, Cancel, ScrollingGroup, Select, Button
from aiogram_dialog.widgets.text import Const, Jinja, Format

from shvatka.tgbot import states
from .getters import (
    get_my_team_,
    get_team_with_players,
    get_selected_player,
    get_team,
    get_forum_teams,
    get_forum_team,
)
from .handlers import (
    rename_team_handler,
    change_desc_team_handler,
    select_player,
    change_permission_handler,
    remove_player_handler,
    change_role_handler,
    change_emoji_handler,
    start_merge,
    select_forum_team,
    confirm_merge,
)

TEAM_PLAYER_CARD = Jinja(
    "Игрок {{selected_player.name_mention}} служит в команде 🚩{{team.name}} "
    "c {{selected_team_player.date_joined | user_timezone}}\n"
    "Сейчас занимает должность "
    "{{selected_team_player|player_emoji}}{{selected_team_player.role}}\n"
)


captains_bridge = Dialog(
    Window(
        Jinja(
            "Капитанский мостик.\n"
            "🚩Команда: <b>{{team.name}}</b>\n"
            "{% if team.description %}"
            "📃Девиз: {{team.description}}\n"
            "{% endif %}"
            "{% if team.captain %}"
            "👑Капитан: {{team.captain.name_mention}}\n"
            "{% endif %}"
        ),
        Cancel(Const("🔙Назад")),
        SwitchTo(
            Const("✍️Переименовать"),
            id="rename",
            state=states.CaptainsBridgeSG.name,
            when=F["team_player"].can_change_team_name,
        ),
        SwitchTo(
            Const("📃Изменить девиз"),
            id="change_desc",
            state=states.CaptainsBridgeSG.description,
            when=F["team_player"].can_change_team_name,
        ),
        SwitchTo(
            Const("👥Игроки"),
            id="players",
            state=states.CaptainsBridgeSG.players,
            when=F["team_player"].can_manage_players | F["team_player"].can_remove_players,
        ),
        Button(
            Const("🔮Былые свершения"),
            id="merge_teams",
            on_click=start_merge,
            when=~F["team"].has_forum_team(),
        ),
        state=states.CaptainsBridgeSG.main,
        getter=get_my_team_,
    ),
    Window(
        Jinja("Переименовать команду 🚩<b>{{team.name}}</b>"),
        SwitchTo(Const("🔙Назад"), id="back", state=states.CaptainsBridgeSG.main),
        TextInput(id="rename", on_success=rename_team_handler),
        getter=get_my_team_,
        state=states.CaptainsBridgeSG.name,
    ),
    Window(
        Jinja("Изменить девиз команды 🚩<b>{{team.name}}</b>"),
        SwitchTo(Const("🔙Назад"), id="back", state=states.CaptainsBridgeSG.main),
        TextInput(id="change_desc", on_success=change_desc_team_handler),
        getter=get_my_team_,
        state=states.CaptainsBridgeSG.description,
    ),
    Window(
        Jinja("Игроки команды 🚩<b>{{team.name}}</b>"),
        SwitchTo(Const("🔙Назад"), id="back", state=states.CaptainsBridgeSG.main),
        ScrollingGroup(
            Select(
                Jinja("{{item|player_emoji}}{{item.player.name_mention}}"),
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
        TEAM_PLAYER_CARD,
        SwitchTo(Const("⤴В меню команды"), id="to_main", state=states.CaptainsBridgeSG.main),
        SwitchTo(Const("🔙Назад"), id="back", state=states.CaptainsBridgeSG.players),
        Button(
            Format("{can_manage_waivers}Подавать вейверы"),
            id="can_manage_waivers",
            on_click=change_permission_handler,
            when=F["team_player"].can_manage_players & F["team_player"].can_manage_waivers,
        ),
        Button(
            Format("{can_manage_players}Управлять игроками"),
            id="can_manage_players",
            on_click=change_permission_handler,
            when=F["team_player"].can_manage_players,
        ),
        Button(
            Format("{can_change_team_name}Переименовывать команду"),
            id="can_change_team_name",
            on_click=change_permission_handler,
            when=F["team_player"].can_manage_players & F["team_player"].can_change_team_name,
        ),
        Button(
            Format("{can_add_players}Добавлять игроков"),
            id="can_add_players",
            on_click=change_permission_handler,
            when=F["team_player"].can_manage_players & F["team_player"].can_add_players,
        ),
        Button(
            Format("{can_remove_players}Удалять игроков"),
            id="can_remove_players",
            on_click=change_permission_handler,
            when=F["team_player"].can_manage_players & F["team_player"].can_remove_players,
        ),
        SwitchTo(
            Const("Изменить должность"),
            id="to_role",
            state=states.CaptainsBridgeSG.player_role,
            when=F["team_player"].can_manage_players,
        ),
        SwitchTo(
            Const("Изменить emoji"),
            id="to_emoji",
            state=states.CaptainsBridgeSG.player_emoji,
            when=F["team_player"].can_manage_players,
        ),
        SwitchTo(
            Const("Изгнать"),
            id="delete",
            state=states.CaptainsBridgeSG.confirm_delete,
            when=F["team_player"].can_remove_players,
        ),
        getter=get_selected_player,
        state=states.CaptainsBridgeSG.player,
    ),
    Window(
        TEAM_PLAYER_CARD,
        Const(
            "Вы уверены что хотите изгнать его из команды?",
        ),
        SwitchTo(Const("⤴В меню команды"), id="to_main", state=states.CaptainsBridgeSG.main),
        SwitchTo(
            Const("⤴Назад к списку игроков"),
            id="to_players",
            state=states.CaptainsBridgeSG.players,
        ),
        SwitchTo(Const("Нет!"), id="back", state=states.CaptainsBridgeSG.player),
        Button(Const("Да, удалить"), id="delete", on_click=remove_player_handler),
        getter=get_selected_player,
        state=states.CaptainsBridgeSG.confirm_delete,
    ),
    Window(
        TEAM_PLAYER_CARD,
        Const("Какую роль ему нужно присвоить?"),
        TextInput(
            id="role_changer",
            on_success=change_role_handler,
        ),
        SwitchTo(Const("⤴В меню команды"), id="to_main", state=states.CaptainsBridgeSG.main),
        SwitchTo(
            Const("⤴Назад к списку игроков"),
            id="to_players",
            state=states.CaptainsBridgeSG.players,
        ),
        getter=get_selected_player,
        state=states.CaptainsBridgeSG.player_role,
    ),
    Window(
        TEAM_PLAYER_CARD,
        Const("Какой emoji должен отображаться перед его ником?"),
        TextInput(
            id="emoji_changer",
            on_success=change_emoji_handler,
        ),
        SwitchTo(Const("⤴В меню команды"), id="to_main", state=states.CaptainsBridgeSG.main),
        SwitchTo(
            Const("⤴Назад к списку игроков"),
            id="to_players",
            state=states.CaptainsBridgeSG.players,
        ),
        getter=get_selected_player,
        state=states.CaptainsBridgeSG.player_emoji,
    ),
)

merge_teams_dialog = Dialog(
    Window(
        Jinja(
            "🔮 Былые свершения.\n"
            "\n"
            "Чтобы вспомнить былые свершения нужно найти команду, как она выглядела на форуме.\n"
            "Хочешь объединить команду {{team.name}} со своей форумной копией?"
        ),
        Cancel(Const("🔙Ой нет, это я случайно")),
        SwitchTo(
            Const("Да, время выбирать"),
            id="to_forum_list",
            state=states.MergeTeams.list_forum,
        ),
        getter=get_team,
        state=states.MergeTeams.main,
    ),
    Window(
        Jinja("Итак мы ищем форумную версию для команды {{team.name}}"),
        Cancel(Const("🔙Не надо ничего объединять")),
        ScrollingGroup(
            Select(
                Jinja("🚩{{item.name}}"),
                id="forum_teams",
                item_id_getter=lambda x: x.id,
                items="forum_teams",
                on_click=select_forum_team,
            ),
            id="forum_teams_sg",
            width=1,
            height=10,
        ),
        getter=(get_team, get_forum_teams),
        state=states.MergeTeams.list_forum,
    ),
    Window(
        Jinja(
            "Объединяем команду <b>{{team.name}}</b> в боте "
            "с командой на форуме <b>{{forum_team.name}}</b>?"
        ),
        Cancel(Const("🔙Не надо ничего объединять")),
        Button(
            Const("Да, объединить"),
            id="confirm_merge",
            on_click=confirm_merge,
        ),
        Cancel(Const("🔙Нет!!")),
        getter=(get_team, get_forum_team),
        state=states.MergeTeams.confirm,
    ),
)
