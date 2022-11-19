from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services import organizers
from shvatka.services.game import get_game
from shvatka.services.level import get_by_id


async def get_level_id(dialog_manager: DialogManager, **_):
    data = dialog_manager.start_data
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    author: dto.Player = dialog_manager.middleware_data["player"]
    level = await get_by_id(data["level_id"], author, dao.level)
    return {
        "level": level,
    }


async def get_orgs(dialog_manager: DialogManager, **_):
    level_id = dialog_manager.start_data["level_id"]
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    author: dto.Player = dialog_manager.middleware_data["player"]
    level = await get_by_id(level_id, author, dao.level)
    game = await get_game(id_=level.game_id, author=author, dao=dao.game)
    orgs = await organizers.get_secondary_orgs(game, dao.organizer)
    return {
        "game": game,
        "orgs": orgs,
    }
