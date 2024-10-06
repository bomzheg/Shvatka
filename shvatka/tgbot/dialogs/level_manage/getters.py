from aiogram_dialog import DialogManager

from shvatka.core.models import dto
from shvatka.core.services import organizers
from shvatka.core.services.game import get_game
from shvatka.core.services.level import get_by_id, get_level_by_id_for_org, get_all_my_free_levels
from shvatka.core.services.organizers import get_org_by_id, get_by_player
from shvatka.infrastructure.db.dao.holder import HolderDao


async def get_level_id(dao: HolderDao, dialog_manager: DialogManager, **_):
    author: dto.Player = dialog_manager.middleware_data["player"]
    level, org = await get_level_and_org(author, dao, dialog_manager)
    hints = level.scenario.time_hints
    return {
        "level": level,
        "time_hints": hints,
        "org": org,
    }


async def get_orgs(dao: HolderDao, dialog_manager: DialogManager, **_):
    level_id = dialog_manager.start_data["level_id"]
    author: dto.Player = dialog_manager.middleware_data["player"]
    level = await get_by_id(level_id, author, dao.level)
    game = await get_game(id_=level.game_id, author=author, dao=dao.game)
    orgs = await organizers.get_secondary_orgs(game, dao.organizer)
    return {
        "game": game,
        "orgs": orgs,
        "level": level,
    }


async def get_level_and_org(
    author: dto.Player,
    dao: HolderDao,
    manager: DialogManager,
) -> tuple[dto.Level, dto.Organizer | None]:
    if "org_id" in manager.start_data:
        org = await get_org_by_id(manager.start_data["org_id"], dao.organizer)
        level = await get_level_by_id_for_org(manager.start_data["level_id"], org, dao.level)
    else:
        level = await get_by_id(manager.start_data["level_id"], author, dao.level)
        org = await get_org(author, level, dao)
    return level, org


async def get_levels(
    player: dto.Player,
    dao: HolderDao,
    **_,
):
    levels = await get_all_my_free_levels(player, dao.level)
    return {"levels": levels}


async def get_org(author: dto.Player, level: dto.Level, dao: HolderDao) -> dto.Organizer | None:
    if level.game_id:
        game = await get_game(level.game_id, author=author, dao=dao.game)
        return await get_by_player(author, game, dao.organizer)
    else:
        return None
