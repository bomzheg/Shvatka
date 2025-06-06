from aiogram import Router

from .dialogs import (
    level,
    keys_dialog,
    hints_dialog,
    level_edit_dialog,
    sly_keys_dialog,
    bonus_hint_dialog,
    routed_conditions_dialog,
)


def setup(router: Router):
    router.include_router(level)
    router.include_router(keys_dialog)
    router.include_router(hints_dialog)
    router.include_router(level_edit_dialog)
    router.include_router(sly_keys_dialog)
    router.include_router(bonus_hint_dialog)
    router.include_router(routed_conditions_dialog)
