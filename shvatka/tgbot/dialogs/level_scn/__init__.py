from aiogram import Router

from .dialogs import level, keys_dialog, hints_dialog, level_edit_dialog, sly_keys_dialog


def setup(router: Router):
    router.include_router(level)
    router.include_router(keys_dialog)
    router.include_router(hints_dialog)
    router.include_router(level_edit_dialog)
    router.include_router(sly_keys_dialog)
