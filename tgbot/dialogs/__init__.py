from aiogram_dialog import DialogRegistry

from tgbot.dialogs.dialogs import games


def setup_dialogs(registry: DialogRegistry):
    registry.register(games)
