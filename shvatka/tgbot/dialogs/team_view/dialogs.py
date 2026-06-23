from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Cancel, SwitchTo, Button
from aiogram_dialog.widgets.text import Const, Format, Jinja, Case

from shvatka.tgbot import states
from .getters import teams_getter, team_getter, filter_getter
from .handlers import (
    select_team,
    select_player,
    change_active_filter,
    change_archive_filter,
    on_start_my_team,
    on_leave_team,
)
from shvatka.tgbot.dialogs.common import BOOL_VIEW

team_view = Dialog(
    Window(
        Jinja(
            "Отфильтрованный список команд\n\n"
            "{{active|bool_emoji}} Активные\n"
            "{{archive|bool_emoji}} Архивные"
        ),
        SwitchTo(Const("🔣Фильтр"), state=states.TeamsSg.filter, id="to_filter"),
        ScrollingGroup(
            Select(
                Format("🚩{item.name}"),
                id="teams",
                item_id_getter=lambda x: x.id,
                items="teams",
                on_click=select_team,
            ),
            id="teams_sg",
            width=1,
            height=10,
        ),
        Cancel(Const("🔙Назад")),
        getter=teams_getter,
        state=states.TeamsSg.list,
    ),
    Window(
        Jinja(
            "Команда: {{team.name }} \n"
            "Капитан: {{team.captain.name_mention}}\n"
            "Сыгранные игры: {{' '.join(game_numbers)}}"
        ),
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
        SwitchTo(Const("🔙Назад"), state=states.TeamsSg.list, id="to_list"),
        Cancel(Const("🔙Выход")),
        getter=team_getter,
        state=states.TeamsSg.one,
    ),
    Window(
        Const("Отметь типы команд для отображения"),
        Button(
            Case(BOOL_VIEW, selector="active") + Const("Активные"),
            id="active",
            on_click=change_active_filter,
        ),
        Button(
            Case(BOOL_VIEW, selector="archive") + Const("Архивные"),
            id="archive",
            on_click=change_archive_filter,
        ),
        SwitchTo(Const("🔙Назад"), state=states.TeamsSg.list, id="to_list"),
        getter=filter_getter,
        state=states.TeamsSg.filter,
    ),
)


my_team_view = Dialog(
    Window(
        Jinja(
            "Моя команда: {{team.name }} \n"
            "Наш капитан: {{team.captain.name_mention}}\n"
            "Сыгранные игры: {{' '.join(game_numbers)}}"
        ),
        Button(Const("☄️Выйти из команды"), id="leave_team", on_click=on_leave_team),
        Cancel(Const("🔙Назад")),
        getter=team_getter,
        state=states.MyTeamSg.team,
    ),
    on_start=on_start_my_team,
)
