from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.level import get_by_id


async def get_level_id(dialog_manager: DialogManager, **_):
    data = dialog_manager.start_data
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    author: dto.Player = dialog_manager.middleware_data["player"]
    level = await get_by_id(data["level_id"], author, dao.level)
    return {
        "level": level,
    }
