from aiogram import Router

from .dialogs import player_dialog


def setup(router: Router):
    router.include_router(player_dialog)
