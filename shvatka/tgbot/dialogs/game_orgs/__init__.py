from aiogram import Router

from .dialogs import game_orgs


def setup(router: Router):
    router.include_router(game_orgs)
