from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import get_team_player, get_my_team, get_team_players


async def get_my_team_(dao: HolderDao, player: dto.Player, **_) -> dict[str, dto.Team]:
    team = await get_my_team(player=player, dao=dao.team_player)
    team_player = await get_team_player(player=player, team=team, dao=dao.team_player)
    return {"team": team, "team_player": team_player}


async def get_team_with_players(dao: HolderDao, player: dto.Player, **_) -> dict[str, dto.Team]:
    team = await get_my_team(player=player, dao=dao.team_player)
    team_player = await get_team_player(player=player, team=team, dao=dao.team_player)
    players = await get_team_players(team=team, dao=dao.team_player)
    return {
        "team": team,
        "team_player": team_player,
        "players": players,
    }


async def get_selected_player(dao: HolderDao, dialog_manager: DialogManager, **_):
    player = await dao.player.get_by_id(dialog_manager.dialog_data["selected_player_id"])
    return {
        "selected_player": player,
    }
