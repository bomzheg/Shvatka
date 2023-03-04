from aiogram_dialog import DialogManager

from src.infrastructure.db.dao.holder import HolderDao
from src.shvatka.models import dto
from src.shvatka.services.player import get_full_team_player, get_my_team, get_team_players
from src.shvatka.utils.exceptions import PlayerNotInTeam
from src.shvatka.views.texts import PERMISSION_EMOJI


async def get_my_team_(dao: HolderDao, player: dto.Player, **_) -> dict[str, dto.Team]:
    try:
        team = await get_my_team(player=player, dao=dao.team_player)
        team_player = await get_full_team_player(player=player, team=team, dao=dao.team_player)
    except PlayerNotInTeam:
        team = None
        team_player = None
    return {"team": team, "team_player": team_player}


async def get_team_with_players(dao: HolderDao, player: dto.Player, **_) -> dict[str, dto.Team]:
    team = await get_my_team(player=player, dao=dao.team_player)
    team_player = await get_full_team_player(player=player, team=team, dao=dao.team_player)
    players = await get_team_players(team=team, dao=dao.team_player)
    return {
        "team": team,
        "team_player": team_player,
        "players": [tp for tp in players if tp.player.id not in (team.captain.id, player.id)],
    }


async def get_selected_player(
    dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **_
):
    team = await get_my_team(player=player, dao=dao.team_player)
    team_player = await get_full_team_player(player=player, team=team, dao=dao.team_player)
    selected_player = await dao.player.get_by_id(dialog_manager.dialog_data["selected_player_id"])
    selected_team_player = await get_full_team_player(selected_player, team, dao.team_player)
    return {
        "selected_player": selected_player,
        "selected_team_player": selected_team_player,
        "team": team,
        "team_player": team_player,
        **{
            key.name: PERMISSION_EMOJI[value]
            for key, value in selected_team_player.permissions.items()
        },
    }
