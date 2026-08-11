from typing import Any

from aiogram_dialog import DialogManager

from shvatka.core.interfaces.identity import IdentityProvider
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from shvatka.core.players.player import get_full_team_player, get_my_team, get_team_players
from shvatka.core.utils.exceptions import PlayerNotInTeam
from shvatka.core.views.texts import PERMISSION_EMOJI
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def get_my_team_(
    dao: HolderDao, identity: FromDishka[IdentityProvider], **_
) -> dict[str, Any]:
    player = await identity.get_required_player()
    try:
        team = await get_my_team(player=player, dao=dao.team_player)
        team_player = await get_full_team_player(player=player, team=team, dao=dao.team_player)
    except PlayerNotInTeam:
        team = None
        team_player = None
    return {"team": team, "team_player": team_player}


@inject
async def get_team_with_players(
    dao: HolderDao, identity: FromDishka[IdentityProvider], **_
) -> dict[str, Any]:
    player = await identity.get_required_player()
    team = await get_my_team(player=player, dao=dao.team_player)
    assert team
    team_player = await get_full_team_player(player=player, team=team, dao=dao.team_player)
    players = await get_team_players(team=team, dao=dao.team_player)
    excluded = [player.id]
    if team.captain:
        excluded.append(team.captain.id)
    return {
        "team": team,
        "team_player": team_player,
        "players": [tp for tp in players if tp.player.id not in excluded],
    }


@inject
async def get_selected_player(
    dao: HolderDao,
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    **_,
):
    player = await identity.get_required_player()
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
