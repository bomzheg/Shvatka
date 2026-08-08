from aiogram import Router

from .dialogs import game_release


def setup(router: Router):
    router.include_router(game_release)
