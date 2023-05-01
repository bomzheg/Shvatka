from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Cancel, SwitchTo, Button
from aiogram_dialog.widgets.text import Const, Format, Jinja, Case

from shvatka.tgbot import states
from .getters import teams_getter, team_getter, filter_getter
from .handlers import select_team, select_player, change_active_filter, change_archive_filter
from ..common import BOOL_VIEW

team_view = Dialog(
    Window(
        Jinja(
            "Отфильтрованный список команд\n\n"
            "{{active|bool_emoji}} Активные\n"
            "{{archive|bool_emoji}} Архивные"
        ),
        Cancel(Const("🔙Назад")),
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
        getter=teams_getter,
        state=states.TeamsSg.list,
    ),
    Window(
        Jinja(
            "Команда: {{team.name }} \n"
            "Капитан: {{team.captain.name_mention}}\n"
            "Сыгранные игры: {{' '.join(game_numbers)}}"
        ),
        Cancel(Const("⤴Выход")),
        SwitchTo(Const("🔙Назад"), state=states.TeamsSg.list, id="to_list"),
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
        getter=team_getter,
        state=states.TeamsSg.one,
    ),
    Window(
        Const("Отметь типы команд для отображения"),
        SwitchTo(Const("🔙Назад"), state=states.TeamsSg.list, id="to_list"),
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
        getter=filter_getter,
        state=states.TeamsSg.filter,
    ),
)
