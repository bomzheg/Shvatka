from aiogram_dialog import DialogRegistry

from tgbot.dialogs import game_manage, level_scn, time_hint


def setup_dialogs(registry: DialogRegistry):
    game_manage.setup(registry)
    level_scn.setup(registry)
    time_hint.setup(registry)
