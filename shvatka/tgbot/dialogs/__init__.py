import asyncio

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram_dialog import Dialog, setup_dialogs
from aiogram_dialog.api.protocols import BgManagerFactory, MessageManagerProtocol
from aiogram_dialog.manager.message_manager import MessageManager
from aiogram_dialog.tools import render_transitions

from shvatka.tgbot.dialogs import (
    effects,
    game_manage,
    game_orgs,
    game_publish,
    game_release,
    game_scn,
    game_spy,
    level_manage,
    level_scn,
    main_menu,
    merge,
    player_view,
    profile,
    starters,
    team_manage,
    team_view,
    time_hint,
    timers,
)
from shvatka.tgbot.dialogs.outdated import OutdatedDialogMiddleware
from shvatka.tgbot.dialogs.preview import render_dialogs_preview
from shvatka.tgbot.filters import GameStatusFilter

DIALOG_PACKAGES = (
    starters,
    main_menu,
    profile,
    game_manage,
    game_scn,
    level_scn,
    time_hint,
    level_manage,
    game_orgs,
    game_publish,
    team_manage,
    merge,
    team_view,
    player_view,
    timers,
    effects,
    game_spy,
)


def collect_all_dialogs() -> list[Dialog]:
    """Every dialog of the bot, without attaching it to a router.

    Dialogs are module-level singletons, so `setup` can run only once per
    process - which the bot itself does. Tools that only need to read the
    dialogs (the preview) go through here instead.
    """
    found: dict[int, Dialog] = {}
    for package in DIALOG_PACKAGES:
        for obj in vars(package).values():
            if isinstance(obj, Dialog):
                found.setdefault(id(obj), obj)
    return list(found.values())


def setup(router: Router, message_manager: MessageManagerProtocol) -> BgManagerFactory:
    dialogs_router = Router(name=__name__)
    dialogs_router.message.filter(F.chat.type == ChatType.PRIVATE)

    dialogs_router.include_router(starters.setup())
    dialogs_router.include_router(setup_all_dialogs())
    dialogs_router.include_router(setup_active_game_dialogs())

    bg_manager = setup_dialogs(dialogs_router, message_manager=message_manager)
    setup_outdated_dialogs(dialogs_router)
    router.include_router(dialogs_router)
    return bg_manager


def setup_outdated_dialogs(dialogs_router: Router) -> None:
    """Let any dialog handler or getter bail out by raising `DialogOutdated`.

    Must run after `setup_dialogs`: inner middlewares are applied in
    registration order, and this one needs `dialog_manager` in the data, which
    aiogram_dialog's own middleware puts there.
    """
    middleware = OutdatedDialogMiddleware()
    dialogs_router.callback_query.middleware(middleware)
    dialogs_router.message.middleware(middleware)


def setup_all_dialogs() -> Router:
    router = Router(name=__name__ + ".common")
    router.callback_query.filter(GameStatusFilter(running=False))
    router.message.filter(GameStatusFilter(running=False))

    main_menu.setup(router)
    profile.setup(router)
    game_manage.setup(router)
    game_scn.setup(router)
    level_scn.setup(router)
    time_hint.setup(router)
    level_manage.setup(router)
    game_orgs.setup(router)
    game_publish.setup(router)
    game_release.setup(router)
    team_manage.setup(router)
    merge.setup(router)
    team_view.setup(router)
    player_view.setup(router)
    timers.setup(router)
    effects.setup(router)

    return router


def setup_active_game_dialogs() -> Router:
    router = Router(name=__name__ + ".game.running")
    game_spy.setup(router)
    return router


def render_all():
    # preview first: it needs no graphviz, so it is produced even without `dot`
    asyncio.run(render_dialogs_preview(collect_all_dialogs()))
    router = Router(name="main")
    setup(router, MessageManager())
    render_transitions(router, title="Shvatka", filename="out/shvatka-dialogs")


if __name__ == "__main__":
    render_all()
