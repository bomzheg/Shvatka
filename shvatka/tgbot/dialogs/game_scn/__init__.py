from aiogram import Router

from .dialogs import game_editor, game_writer


def setup(router: Router):
    router.include_router(game_writer)
    router.include_router(game_editor)
