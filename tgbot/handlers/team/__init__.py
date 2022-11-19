from aiogram import Router

from tgbot.utils.router import disable_router_on_game
from .manage import setup_team_manage


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)
    router.include_router(setup_team_manage())
    return router
