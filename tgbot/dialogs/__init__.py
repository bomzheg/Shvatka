from aiogram_dialog import DialogRegistry

from tgbot.dialogs import (
    game_manage, level_scn, time_hint, game_scn, level_manage, game_orgs,
    game_spy, main_menu, game_publish,
)


def setup_dialogs(registry: DialogRegistry):
    main_menu.setup(registry)
    game_manage.setup(registry)
    game_scn.setup(registry)
    level_scn.setup(registry)
    time_hint.setup(registry)
    level_manage.setup(registry)
    game_orgs.setup(registry)
    game_spy.setup(registry)
    game_publish.setup(registry)
