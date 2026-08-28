from typing import Any

from aiogram_dialog import DialogManager

from shvatka.common.config.models.main import FeaturesConfig
from shvatka.core.interfaces.identity import IdentityProvider
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from shvatka.core.models import dto
from shvatka.core.services import organizers
from shvatka.core.services.game import get_game
from shvatka.core.services.level import get_by_id, get_level_by_id_for_org, get_all_my_free_levels
from shvatka.core.services.organizers import get_org_by_id, get_by_player
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def get_level_id(
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    features: FromDishka[FeaturesConfig],
    **_,
):
    author = await identity.get_required_player()
    level, org = await get_level_and_org(author, dao, dialog_manager)
    hints_ = level.scenario.time_hints
    return {
        "level": level,
        "enabled_test": features.level_test,
        "time_hints": hints_,
        "org": org,
    }


@inject
async def get_orgs(
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    **_,
):
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    level_id = data["level_id"]
    author = await identity.get_required_player()
    level = await get_by_id(level_id, author, dao.level)
    if level.game_id is not None:
        game = await get_game(id_=level.game_id, author=author, dao=dao.game)
        orgs = await organizers.get_secondary_orgs(game, dao.organizer)
    else:
        game = None
        orgs = []
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
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    if "org_id" in data:
        org = await get_org_by_id(data["org_id"], dao.organizer)
        level = await get_level_by_id_for_org(data["level_id"], org, dao.level)
        return level, org
    level = await get_by_id(data["level_id"], author, dao.level)
    org_ = await get_org(author, level, dao)
    return level, org_


@inject
async def get_levels(
    dao: FromDishka[HolderDao],
    identity: FromDishka[IdentityProvider],
    **_,
):
    levels = await get_all_my_free_levels(await identity.get_required_player(), dao.level)
    return {"levels": levels}


async def get_org(author: dto.Player, level: dto.Level, dao: HolderDao) -> dto.Organizer | None:
    if level.game_id:
        game = await get_game(level.game_id, author=author, dao=dao.game)
        return await get_by_player(author, game, dao.organizer)
    return None
