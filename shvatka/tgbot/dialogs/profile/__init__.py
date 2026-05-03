from aiogram import Router

from .dialogs import profile_dialog


def setup(router: Router):
    router.include_router(profile_dialog)
