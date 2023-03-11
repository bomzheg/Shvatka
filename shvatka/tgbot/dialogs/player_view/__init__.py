from aiogram_dialog import DialogRegistry

from .dialogs import player_dialog


def setup(registry: DialogRegistry):
    registry.register(player_dialog)
