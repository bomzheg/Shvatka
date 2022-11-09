from aiogram_dialog import DialogRegistry

from tgbot.dialogs import game_manage, level_scn, time_hint, game_scn, level_manage


def setup_dialogs(registry: DialogRegistry):
    game_manage.setup(registry)
    game_scn.setup(registry)
    level_scn.setup(registry)
    time_hint.setup(registry)
    level_manage.setup(registry)
