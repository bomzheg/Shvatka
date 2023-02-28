from aiogram import Dispatcher, Router
from aiogram_dialog import DialogRegistry

from tgbot.dialogs import (
    game_manage,
    level_scn,
    time_hint,
    game_scn,
    level_manage,
    game_orgs,
    game_spy,
    main_menu,
    game_publish,
    team_manage,
)
from tgbot.filters import GameStatusFilter


def setup(registry: DialogRegistry, dp: Dispatcher):
    dialogs_router = Router(name="tgbot.dialogs.common")

    dialogs_router.callback_query.filter(GameStatusFilter(running=False))
    dialogs_router.message.filter(GameStatusFilter(running=False))

    setup_dialogs(registry)
    dp.include_router(setup_active_game_dialogs(registry))
    registry.setup_dp(dp, default_router=dialogs_router)


def setup_dialogs(registry: DialogRegistry):
    main_menu.setup(registry)
    game_manage.setup(registry)
    game_scn.setup(registry)
    level_scn.setup(registry)
    time_hint.setup(registry)
    level_manage.setup(registry)
    game_orgs.setup(registry)
    game_publish.setup(registry)
    team_manage.setup(registry)


def setup_active_game_dialogs(registry: DialogRegistry) -> Router:
    router = Router(name="tgbot.dialogs.game.running")
    game_spy.setup(registry, router)
    return router
