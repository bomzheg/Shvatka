from aiogram import Router

from .dialogs import time_hint


def setup(router: Router):
    router.include_router(time_hint)
