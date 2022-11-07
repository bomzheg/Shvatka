from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.level import get_all_my_levels


def get_game_name(dialog_manager: DialogManager, **_):
    data = dialog_manager.dialog_data
    return {
        "game_name": data["game_name"],
    }


async def select_my_levels(dialog_manager: DialogManager, **_):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    author: dto.Player = dialog_manager.middleware_data["player"]
    levels = await get_all_my_levels(author, dao.level)
    return {
        "levels": filter(lambda l: l.game_id is None, levels),
    }
