from aiogram import Router

from .dialogs import game_spy


def setup(router: Router):
    router.include_router(game_spy)
