from aiogram import Router

from .dialogs import game_writer, game_editor


def setup(router: Router):
    router.include_router(game_writer)
    router.include_router(game_editor)
