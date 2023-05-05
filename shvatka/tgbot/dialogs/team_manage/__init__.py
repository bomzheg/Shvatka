from aiogram_dialog import DialogRegistry

from .dialogs import captains_bridge


def setup(registry: DialogRegistry):
    registry.register(captains_bridge)
