from aiogram_dialog import DialogRegistry

from .dialogs import game_publish


def setup(registry: DialogRegistry):
    registry.register(game_publish)
