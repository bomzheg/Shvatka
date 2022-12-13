from aiogram_dialog import DialogRegistry

from .dialogs import my_games, schedule_game_dialog, games


def setup(registry: DialogRegistry):
    registry.register(games)
    registry.register(my_games)
    registry.register(schedule_game_dialog)
