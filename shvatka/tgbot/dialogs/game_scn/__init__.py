from aiogram_dialog import DialogRegistry

from .dialogs import game_writer, game_editor


def setup(registry: DialogRegistry):
    registry.register(game_writer)
    registry.register(game_editor)
