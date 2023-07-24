from aiogram import Router

from .dialogs import game_publish


def setup(router: Router):
    router.include_router(game_publish)
