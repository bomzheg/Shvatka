from aiogram_dialog import DialogRegistry

from .dialogs import team_view


def setup(registry: DialogRegistry):
    registry.register(team_view)
