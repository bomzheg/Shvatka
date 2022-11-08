from aiogram_dialog import DialogRegistry

from .dialogs import games, schedule_game_dialog


def setup(registry: DialogRegistry):
    registry.register(games)
    registry.register(schedule_game_dialog)
