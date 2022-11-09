from aiogram_dialog import DialogRegistry

from .dialogs import level_manage


def setup(registry: DialogRegistry):
    registry.register(level_manage)
