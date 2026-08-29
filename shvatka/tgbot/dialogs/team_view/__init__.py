from aiogram import Router

from .dialogs import my_team_view, team_view


def setup(router: Router):
    router.include_router(team_view)
    router.include_router(my_team_view)
