from aiogram import Router

from .dialogs import effects


def setup(router: Router):
    router.include_router(effects)
