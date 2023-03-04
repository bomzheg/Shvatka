from aiogram_dialog import DialogRegistry

from .dialogs import level_manage, level_test_dialog


def setup(registry: DialogRegistry):
    registry.register(level_manage)
    registry.register(level_test_dialog)
