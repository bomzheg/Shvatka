from aiogram_dialog import DialogManager

from shvatka.core.services.team import get_team_by_id, get_team_by_forum_team_id, get_free_forum_teams
from shvatka.infrastructure.db.dao.holder import HolderDao


async def get_team(dao: HolderDao, dialog_manager: DialogManager, **_):
    team_id = dialog_manager.start_data["team_id"]
    team = await get_team_by_id(team_id, dao.team)
    return {
        "team": team,
    }


async def get_forum_team(dao: HolderDao, dialog_manager: DialogManager, **_):
    forum_team_id = dialog_manager.dialog_data["forum_team_id"]
    forum_team = await get_team_by_forum_team_id(forum_team_id, dao.team)
    return {
        "forum_team": forum_team,
    }


async def get_forum_teams(dao: HolderDao, **_):
    return {"forum_teams": await get_free_forum_teams(dao.forum_team)}
