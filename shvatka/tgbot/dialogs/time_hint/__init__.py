from aiogram_dialog import DialogRegistry

from .dialogs import time_hint


def setup(registry: DialogRegistry):
    registry.register(time_hint)
