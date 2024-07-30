from aiogram import Router

from .dialogs import time_hint, time_hint_edit


def setup(router: Router):
    router.include_router(time_hint)
    router.include_router(time_hint_edit)
