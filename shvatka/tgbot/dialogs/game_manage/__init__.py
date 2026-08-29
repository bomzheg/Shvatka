from aiogram import Router

from .dialogs import games, my_games, schedule_game_dialog


def setup(router: Router):
    router.include_router(games)
    router.include_router(my_games)
    router.include_router(schedule_game_dialog)
