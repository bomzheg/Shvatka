from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Cancel
from aiogram_dialog.widgets.text import Format, Const

from tgbot.states import GameOrgs
from .getters import get_orgs
from .handlers import select_org

game_orgs = Dialog(
    Window(
        Format("Список организаторов игры {game.name}"),
        Cancel(Const("Назад")),
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
)
