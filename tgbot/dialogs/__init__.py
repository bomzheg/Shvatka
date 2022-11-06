from aiogram_dialog import DialogRegistry

from tgbot.dialogs import game_manage


def setup_dialogs(registry: DialogRegistry):
    game_manage.setup(registry)
