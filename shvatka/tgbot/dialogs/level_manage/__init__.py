from aiogram_dialog import DialogRegistry

from .dialogs import level_manage, level_test_dialog, levels_list


def setup(registry: DialogRegistry):
    registry.register(levels_list)
    registry.register(level_manage)
    registry.register(level_test_dialog)
