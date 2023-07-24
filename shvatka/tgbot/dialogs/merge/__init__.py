from aiogram import Router

from .dialogs import merge_teams_dialog, merge_player_dialog


def setup(router: Router):
    router.include_router(merge_teams_dialog)
    router.include_router(merge_player_dialog)
