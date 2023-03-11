from aiogram_dialog import DialogManager

from shvatka.core.models import dto
from shvatka.core.services.player import get_team_players
from shvatka.core.services.team import get_teams, get_team_by_id
from shvatka.infrastructure.db.dao.holder import HolderDao


async def teams_getter(dao: HolderDao, **_) -> dict[str, list[dto.Team]]:
    return {"teams": await get_teams(dao.team)}


async def team_getter(dao: HolderDao, dialog_manager: DialogManager, **_):
    team_id: int = dialog_manager.dialog_data["team_id"]
    team = await get_team_by_id(team_id, dao.team)
    players = await get_team_players(team=team, dao=dao.team_player)
    return {
        "team": team,
        "players": [tp for tp in players],
    }
