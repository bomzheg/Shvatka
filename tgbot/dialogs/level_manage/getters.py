from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services import organizers
from shvatka.services.game import get_game
from shvatka.services.level import get_by_id, get_level_by_id_for_org
from shvatka.services.organizers import get_org_by_id


async def get_level_id(dialog_manager: DialogManager, **_):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    author: dto.Player = dialog_manager.middleware_data["player"]
    try:
        org_id = dialog_manager.start_data["org_id"]
    except KeyError:
        level = await get_by_id(dialog_manager.start_data["level_id"], author, dao.level)
    else:
        org = await get_org_by_id(org_id, dao.organizer)
        level = await get_level_by_id_for_org(dialog_manager.start_data["level_id"], org, dao.level)
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
        "level": level,
    }
