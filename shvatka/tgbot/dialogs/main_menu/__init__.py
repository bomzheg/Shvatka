from aiogram_dialog import DialogRegistry

from .dialogs import main_menu, promote_dialog


def setup(registry: DialogRegistry):
    registry.register(main_menu)
    registry.register(promote_dialog)
