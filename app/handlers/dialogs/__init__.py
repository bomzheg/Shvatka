from aiogram_dialog import DialogRegistry

from app.handlers.dialogs.dialogs import games


def setup_dialogs(registry: DialogRegistry):
    registry.register(games)
