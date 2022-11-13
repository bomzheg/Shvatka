from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto


async def get_player(dialog_manager: DialogManager, **_):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player: dto.Player = dialog_manager.middleware_data["player"]
    return {
        "player": player,
    }
