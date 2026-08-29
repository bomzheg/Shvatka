from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    ScrollingGroup,
    Select,
    SwitchInlineQuery,
)
from aiogram_dialog.widgets.text import Const, Format, Jinja, Multi

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.preview_data import (
    PREVIEW_ORG,
    PREVIEW_ORG_PERMISSIONS,
    PREVIEW_ORGS,
    PREVIEW_SIMPLE_GAME,
    PreviewSwitchTo,
)

from .getters import get_org, get_orgs
from .handlers import change_deleted_handler, change_permission_handler, select_org

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
        preview_data={
            "game": PREVIEW_SIMPLE_GAME,
            "orgs": PREVIEW_ORGS,
            "inline_query": "add-game-org-token",
        },
        preview_add_transitions=[PreviewSwitchTo(states.GameOrgsSG.org_menu)],
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
        preview_data={"org": PREVIEW_ORG, **PREVIEW_ORG_PERMISSIONS},
    ),
)
