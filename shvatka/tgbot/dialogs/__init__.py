from aiogram import Router

from shvatka.tgbot.dialogs import (
    game_orgs,
    game_manage,
    player_view,
    merge,
    level_scn,
    time_hint,
    game_scn,
    level_manage,
    game_spy,
    main_menu,
    game_publish,
    team_manage,
    team_view,
)
from shvatka.tgbot.filters import GameStatusFilter


def setup() -> Router:
    dialogs_router = Router(name="tgbot.dialogs")
    dialogs_router.include_router(setup_all_dialogs())
    dialogs_router.include_router(setup_active_game_dialogs())

    return dialogs_router


def setup_all_dialogs() -> Router:
    router = Router(name="tgbot.dialogs.common")
    router.callback_query.filter(GameStatusFilter(running=False))
    router.message.filter(GameStatusFilter(running=False))

    main_menu.setup(router)
    game_manage.setup(router)
    game_scn.setup(router)
    level_scn.setup(router)
    time_hint.setup(router)
    level_manage.setup(router)
    game_orgs.setup(router)
    game_publish.setup(router)
    team_manage.setup(router)
    merge.setup(router)
    team_view.setup(router)
    player_view.setup(router)

    return router


def setup_active_game_dialogs() -> Router:
    router = Router(name="tgbot.dialogs.game.running")
    game_spy.setup(router)
    return router
