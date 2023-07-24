from aiogram import Router

from .dialogs import main_menu, promote_dialog


def setup(router: Router):
    router.include_router(main_menu)
    router.include_router(promote_dialog)
