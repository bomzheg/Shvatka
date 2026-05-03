from aiogram import Router

from .dialogs import profile


def setup(router: Router):
    router.include_router(profile.router)