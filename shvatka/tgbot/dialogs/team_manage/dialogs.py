from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Cancel, ScrollingGroup, Select, Button
from aiogram_dialog.widgets.text import Const, Jinja, Format

from shvatka.tgbot import states
from .getters import (
    get_my_team_,
    get_team_with_players,
    get_selected_player,
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
    send_user_request,
    gotten_user_request,
    remove_user_request,
    send_chat_request,
    gotten_chat_request,
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
            Const("🔀Перенести в другой чат"),
            id="change_chat",
            on_click=send_chat_request,
        ),
        MessageInput(func=gotten_chat_request, filter=F.chat_shared),
        Button(
            Const("🔮Былые свершения команды"),
            id="merge_teams",
            on_click=start_merge,
            when=~F["team"].has_forum_team(),
        ),
        Cancel(Const("🔙Назад")),
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
        SwitchTo(
            Const("Добавить"),
            id="to_add",
            state=states.CaptainsBridgeSG.add_player,
            on_click=send_user_request,
        ),
        SwitchTo(Const("🔙Назад"), id="back", state=states.CaptainsBridgeSG.main),
        getter=get_team_with_players,
        state=states.CaptainsBridgeSG.players,
    ),
    Window(
        Jinja("Чтобы добавить игрока нажми на кнопку в самом внизу, затем выбери пользователя"),
        MessageInput(func=gotten_user_request, filter=F.user_shared|F.contact),
        SwitchTo(
            Const("🔙Назад"),
            id="back",
            state=states.CaptainsBridgeSG.players,
            on_click=remove_user_request,
        ),
        getter=get_my_team_,
        state=states.CaptainsBridgeSG.add_player,
    ),
    Window(
        TEAM_PLAYER_CARD,
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
        SwitchTo(Const("🔙В меню команды"), id="to_main", state=states.CaptainsBridgeSG.main),
        SwitchTo(Const("🔙Назад"), id="back", state=states.CaptainsBridgeSG.players),
        getter=get_selected_player,
        state=states.CaptainsBridgeSG.player,
    ),
    Window(
        TEAM_PLAYER_CARD,
        Const(
            "Вы уверены что хотите изгнать его из команды?",
        ),
        SwitchTo(Const("Нет!"), id="back", state=states.CaptainsBridgeSG.player),
        Button(Const("Да, удалить"), id="delete", on_click=remove_player_handler),
        SwitchTo(Const("🔙В меню команды"), id="to_main", state=states.CaptainsBridgeSG.main),
        SwitchTo(
            Const("🔙Назад к списку игроков"),
            id="to_players",
            state=states.CaptainsBridgeSG.players,
        ),
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
        SwitchTo(Const("🔙В меню команды"), id="to_main", state=states.CaptainsBridgeSG.main),
        SwitchTo(
            Const("🔙Назад к списку игроков"),
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
        SwitchTo(Const("🔙В меню команды"), id="to_main", state=states.CaptainsBridgeSG.main),
        SwitchTo(
            Const("🔙Назад к списку игроков"),
            id="to_players",
            state=states.CaptainsBridgeSG.players,
        ),
        getter=get_selected_player,
        state=states.CaptainsBridgeSG.player_emoji,
    ),
)
