from aiogram import Router
from aiogram_dialog import DialogRegistry

from .dialogs import game_spy


def setup(registry: DialogRegistry, router: Router):
    registry.register(game_spy, router=router)
