from aiogram_dialog import DialogRegistry

from .dialogs import level, keys_dialog, hints_dialog


def setup(registry: DialogRegistry):
    registry.register(level)
    registry.register(keys_dialog)
    registry.register(hints_dialog)
