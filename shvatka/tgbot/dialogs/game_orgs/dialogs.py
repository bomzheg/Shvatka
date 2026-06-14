from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    ScrollingGroup,
    Select,
    Cancel,
    Button,
    Back,
    SwitchInlineQuery,
)
from aiogram_dialog.widgets.text import Format, Const, Multi, Jinja

from shvatka.tgbot import states
from .getters import get_orgs, get_org
from .handlers import select_org, change_permission_handler, change_deleted_handler

game_orgs = Dialog(
    Window(
        Jinja("Список организаторов игры {{game.name}}"),
        SwitchInlineQuery(
            Const("👋Добавить организатора"),
            Format("{inline_query}"),
            when=~F["game"].is_complete(),
        ),
        ScrollingGroup(
            Select(
                Multi(
                    Const("🗑", when=F["item"].deleted),
                    Jinja("{{item.player.name_mention}}"),
                    sep="",
                ),
                id="game_orgs",
                item_id_getter=lambda x: x.id,
                items="orgs",
                on_click=select_org,
            ),
            id="game_orgs_sg",
            width=1,
            height=10,
        ),
        Cancel(Const("🔙Назад")),
        getter=get_orgs,
        state=states.GameOrgsSG.orgs_list,
    ),
    Window(
        Multi(
            Const("🗑", when=F["org"].deleted),
            Jinja(
                "Организатор <b>{{org.player.name_mention}}</b> на игру <b>{{org.game.name}}</b>"
            ),
            sep="",
        ),
        Button(
            Format("{can_spy}Шпионить"),
            id="can_spy",
            on_click=change_permission_handler,
        ),
        Button(
            Format("{can_see_log_keys}Смотреть лог ключей"),
            id="can_see_log_keys",
            on_click=change_permission_handler,
        ),
        Button(
            Format("{view_scenario}Смотреть сценарий"),
            id="view_scenario",
            on_click=change_permission_handler,
        ),
        Button(
            Format("{can_validate_waivers}Принимать вейверы"),
            id="can_validate_waivers",
            on_click=change_permission_handler,
            when="🤡",
        ),
        Button(
            Multi(
                Const("🗑"),
                Const("Удалить", when=~F["org"].deleted),
                Const("Восстановить", when=F["org"].deleted),
                sep="",
            ),
            id="flip_deleted",
            on_click=change_deleted_handler,
        ),
        Back(text=Const("К списку организаторов")),
        getter=get_org,
        state=states.GameOrgsSG.org_menu,
    ),
)
