from aiogram_dialog import DialogRegistry

from .dialogs import game


def setup(registry: DialogRegistry):
    registry.register(game)
