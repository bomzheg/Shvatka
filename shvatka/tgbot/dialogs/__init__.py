from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.protocols import MessageManagerProtocol, BgManagerFactory

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
    starters,
)
from shvatka.tgbot.filters import GameStatusFilter


def setup(router: Router, message_manager: MessageManagerProtocol) -> BgManagerFactory:
    dialogs_router = Router(name=__name__)
    dialogs_router.message.filter(F.chat.type == ChatType.PRIVATE)

    dialogs_router.include_router(starters.setup())
    dialogs_router.include_router(setup_all_dialogs())
    dialogs_router.include_router(setup_active_game_dialogs())

    bg_manager = setup_dialogs(dialogs_router, message_manager=message_manager)
    router.include_router(dialogs_router)
    return bg_manager


def setup_all_dialogs() -> Router:
    router = Router(name=__name__ + ".common")
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
    router = Router(name=__name__ + ".game.running")
    game_spy.setup(router)
    return router
