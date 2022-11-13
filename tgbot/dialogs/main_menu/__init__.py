from aiogram_dialog import DialogRegistry

from .dialogs import main_menu


def setup(registry: DialogRegistry):
    registry.register(main_menu)
