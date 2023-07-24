from aiogram import Router

from .dialogs import level_manage, level_test_dialog, levels_list


def setup(router: Router):
    router.include_router(levels_list)
    router.include_router(level_manage)
    router.include_router(level_test_dialog)
