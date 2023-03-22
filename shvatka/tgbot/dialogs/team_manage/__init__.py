from aiogram_dialog import DialogRegistry

from .dialogs import captains_bridge, merge_teams_dialog


def setup(registry: DialogRegistry):
    registry.register(captains_bridge)
    registry.register(merge_teams_dialog)
