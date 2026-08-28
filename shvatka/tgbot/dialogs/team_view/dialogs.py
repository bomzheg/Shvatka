from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.text import Case, Const, Format, Jinja

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.common import BOOL_VIEW
from shvatka.tgbot.dialogs.preview_data import (
    PREVIEW_TEAM_CARD,
    PREVIEW_TEAMS,
    PreviewStart,
    PreviewSwitchTo,
)

from .getters import filter_getter, my_team_getter, team_getter, teams_getter
from .handlers import (
    change_active_filter,
    change_archive_filter,
    on_leave_team,
    select_player,
    select_team,
)

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
        preview_data={"teams": PREVIEW_TEAMS, "active": True, "archive": False},
        preview_add_transitions=[PreviewSwitchTo(states.TeamsSg.one)],
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
        preview_data=PREVIEW_TEAM_CARD,
        preview_add_transitions=[PreviewStart(states.PlayerSg.main)],
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
        preview_data={"active": True, "archive": False},
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
        getter=my_team_getter,
        state=states.MyTeamSg.team,
        preview_data=PREVIEW_TEAM_CARD,
    ),
)
