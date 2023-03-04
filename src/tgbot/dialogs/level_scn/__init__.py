from aiogram_dialog import DialogRegistry

from .dialogs import level


def setup(registry: DialogRegistry):
    registry.register(level)
