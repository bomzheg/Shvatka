from typing import Any

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.services.team import (
    get_free_forum_teams,
    get_team_by_forum_team_id,
    get_team_by_id,
)
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def get_team(
    dao: FromDishka[HolderDao], dialog_manager: DialogManager, **_
) -> dict[str, Any]:
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    team_id = data["team_id"]
    team = await get_team_by_id(team_id, dao.team)
    return {
        "team": team,
    }


@inject
async def get_forum_team(
    dao: FromDishka[HolderDao], dialog_manager: DialogManager, **_
) -> dict[str, Any]:
    forum_team_id = dialog_manager.dialog_data["forum_team_id"]
    forum_team = await get_team_by_forum_team_id(forum_team_id, dao.team)
    return {
        "forum_team": forum_team,
    }


@inject
async def get_forum_teams(dao: FromDishka[HolderDao], **_) -> dict[str, Any]:
    return {"forum_teams": await get_free_forum_teams(dao.forum_team)}


@inject
async def get_forum_user(
    dao: FromDishka[HolderDao], dialog_manager: DialogManager, **_
) -> dict[str, Any]:
    forum_player_id = dialog_manager.dialog_data["forum_player_id"]
    return {"forum_user": await dao.forum_user.get_by_id(forum_player_id)}
