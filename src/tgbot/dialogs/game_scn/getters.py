from aiogram_dialog import DialogManager

from src.core.models import dto
from src.core.services.game import get_full_game
from src.core.services.level import get_all_my_free_levels
from src.infrastructure.db.dao.holder import HolderDao


async def get_game_name(dialog_manager: DialogManager, **_):
    data = dialog_manager.dialog_data
    return {
        "game_name": data["game_name"],
    }


async def select_my_levels(dialog_manager: DialogManager, **_):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    author: dto.Player = dialog_manager.middleware_data["player"]
    levels = await get_all_my_free_levels(author, dao.level)
    return {
        "levels": levels,
    }


async def select_full_game(dialog_manager: DialogManager, **_):
    id_: int = dialog_manager.start_data["game_id"]
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    author: dto.Player = dialog_manager.middleware_data["player"]
    game = await get_full_game(id_, author, dao.game)
    return {
        "levels": game.levels,
        "game": game,
    }
