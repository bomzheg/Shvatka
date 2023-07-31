from aiogram import Router

from .dialogs import team_view, my_team_view


def setup(router: Router):
    router.include_router(team_view)
    router.include_router(my_team_view)
