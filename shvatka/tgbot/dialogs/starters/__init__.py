from aiogram import Router, F
from aiogram.enums import ChatType

from . import editor, game_spy, info, manage_team, player, stat
from shvatka.tgbot.filters import GameStatusFilter
from shvatka.tgbot.utils.router import disable_router_on_game


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(F.chat.type == ChatType.PRIVATE)

    common_router = router.include_router(Router(name=__name__ + ".common"))
    disable_router_on_game(common_router)

    common_router.include_router(editor.setup())
    common_router.include_router(info.setup())
    common_router.include_router(manage_team.setup())
    common_router.include_router(player.setup())
    common_router.include_router(stat.setup())

    game_router = router.include_router(Router(name=__name__ + ".game"))
    game_router.message.filter(GameStatusFilter(running=True))

    game_router.include_router(game_spy.setup())
    return router
