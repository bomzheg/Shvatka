from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Cancel, Button, Back
from aiogram_dialog.widgets.text import Format, Const

from tgbot.states import GameOrgs
from .getters import get_orgs, get_org
from .handlers import select_org, change_permission_handler
from ..widgets.switch_inline import SwitchInlineQuery

game_orgs = Dialog(
    Window(
        Format("Список организаторов игры {game.name}"),
        Cancel(Const("Назад")),
        SwitchInlineQuery(
            Const("Добавить организатора"),
            Format("{inline_query}"),
        ),
        ScrollingGroup(
            Select(
                Format("{item.player.user.name_mention}"),
                id="game_orgs",
                item_id_getter=lambda x: x.id,
                items="orgs",
                on_click=select_org,
            ),
            id="game_orgs_sg",
            width=1,
            height=10,
        ),
        getter=get_orgs,
        state=GameOrgs.orgs_list,
    ),
    Window(
        Format("Организатор <b>{org.player.user.name_mention}</b> на игру <b>{org.game.name}</b>"),
        Back(text=Const("К списку организаторов")),
        Button(
            Format("{can_spy}Может шпионить"),
            id="can_spy",
            on_click=change_permission_handler,
        ),
        Button(
            Format("{can_see_log_keys}Может смотреть лог ключей"),
            id="can_see_log_keys",
            on_click=change_permission_handler,
        ),
        Button(
            Format("{can_validate_waivers}Может принимать вейверы"),
            id="can_validate_waivers",
            on_click=change_permission_handler,
        ),
        getter=get_org,
        state=GameOrgs.org_menu,
    ),
)
