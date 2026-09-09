from aiogram import Router

from .dialogs import season


def setup(router: Router):
    router.include_router(season)
