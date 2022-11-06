from aiogram_dialog import DialogRegistry

from .dialogs import games


def setup(registry: DialogRegistry):
    registry.register(games)
