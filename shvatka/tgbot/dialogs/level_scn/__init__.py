from aiogram import Router

from .dialogs import (
    effects_key_dialog,
    hints_dialog,
    key_effects_condition_dialog,
    keys_dialog,
    level,
    level_edit_dialog,
)


def setup(router: Router):
    router.include_router(level)
    router.include_router(keys_dialog)
    router.include_router(hints_dialog)
    router.include_router(level_edit_dialog)
    router.include_router(effects_key_dialog)
    router.include_router(key_effects_condition_dialog)
