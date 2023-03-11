from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Cancel, SwitchTo
from aiogram_dialog.widgets.text import Const, Format, Jinja

from shvatka.tgbot import states
from .getters import teams_getter, team_getter
from .handlers import select_team

team_view = Dialog(
    Window(
        Const("Список команд"),
        Cancel(Const("⤴Назад")),
        ScrollingGroup(
            Select(
                Format("{item.name}"),
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
        Jinja("Команда {{team.name }} \n" "Капитан {{team.captain.name_mention}}"),
        Cancel(Const("⤴Выход")),
        SwitchTo(Const("⤴Назад"), state=states.TeamsSg.list, id="to_team_list"),
        ScrollingGroup(
            Select(
                Format("{item.player.name_mention}"),
                id="players",
                item_id_getter=lambda x: x.id,
                items="players",
            ),
            id="players_sg",
            width=1,
            height=10,
        ),
        getter=team_getter,
        state=states.TeamsSg.one,
    ),
)
