from typing import Any

from aiogram_dialog import DialogManager

from shvatka.common.config.models.main import FeaturesConfig
from shvatka.core.interfaces.identity import IdentityProvider
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from shvatka.core.players.player import get_team_players
from shvatka.core.views.texts import PERMISSION_EMOJI
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.dialogs.outdated import get_actual_team_player, get_actual_teammate


@inject
async def get_my_team_(identity: FromDishka[IdentityProvider], feature: FromDishka[FeaturesConfig], **_) -> dict[str, Any]:
    team_player = await get_actual_team_player(identity)
    return {
        "team": team_player.team,
        "team_player": team_player,
        "merge_team": feature.merge_team_button,
    }


@inject
async def get_team_with_players(
    dao: FromDishka[HolderDao], identity: FromDishka[IdentityProvider], **_
) -> dict[str, Any]:
    team_player = await get_actual_team_player(identity)
    team = team_player.team
    players = await get_team_players(team=team, dao=dao.team_player)
    excluded = [team_player.player.id]
    if team.captain:
        excluded.append(team.captain.id)
    return {
        "team": team,
        "team_player": team_player,
        "players": [tp for tp in players if tp.player.id not in excluded],
    }


@inject
async def get_selected_player(
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    **_,
):
    team_player = await get_actual_team_player(identity)
    team = team_player.team
    selected_player = await dao.player.get_by_id(dialog_manager.dialog_data["selected_player_id"])
    selected_team_player = await get_actual_teammate(selected_player, team, dao.team_player)
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
