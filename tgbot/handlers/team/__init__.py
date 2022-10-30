from aiogram import Router

from .manage import setup_team_manage


def setup() -> Router:
    router = Router(name=__name__)
    router.include_router(setup_team_manage())
    return router
