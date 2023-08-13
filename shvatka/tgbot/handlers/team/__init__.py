from aiogram import Router

from shvatka.tgbot.utils.router import disable_router_on_game
from . import manage


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)
    router.include_router(manage.setup())
    return router
