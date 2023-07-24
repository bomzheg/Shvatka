from aiogram import Router

from .dialogs import team_view


def setup(router: Router):
    router.include_router(team_view)
