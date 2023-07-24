from aiogram import Router

from .dialogs import captains_bridge


def setup(router: Router):
    router.include_router(captains_bridge)
