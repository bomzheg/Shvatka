from aiogram_dialog import DialogRegistry

from .dialogs import game_orgs


def setup(registry: DialogRegistry):
    registry.register(game_orgs)
