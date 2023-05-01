from aiogram_dialog import DialogRegistry

from .dialogs import merge_teams_dialog


def setup(registry: DialogRegistry):
    registry.register(merge_teams_dialog)
