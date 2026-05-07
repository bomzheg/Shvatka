from typing import Any

from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.common import Config
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.players.player import get_player_with_stat, get_teams_history
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def player_stat_getter(
    dao: HolderDao, identity: FromDishka[IdentityProvider], **_
) -> dict[str, Any]:
    player_common = await identity.get_required_player()
    player = await get_player_with_stat(player_common.id, dao.player)
    correct_keys_percent = (
        player.typed_correct_keys_count / player.typed_keys_count if player.typed_keys_count else 0
    )
    return {
        "player": player,
        "correct_keys": correct_keys_percent,
        "history": await get_teams_history(player, dao.team_player),
    }


@inject
async def player_getter(
    identity: FromDishka[IdentityProvider],
    **_,
) -> dict[str, Any]:
    player = await identity.get_required_player()
    return {
        "player": player,
    }


@inject
async def player_one_time_url_getter(
    identity: FromDishka[IdentityProvider],
    config_: FromDishka[Config],
    holder: FromDishka[HolderDao],
    **_,
) -> dict[str, Any]:
    player = await identity.get_required_player()
    token = await holder.one_time_token.save_new_token(dct={"player_id": player.id})
    return {
        "player": player,
        "token": f"{config_.web.base_url}/auth/one-time-token?token={token}",
    }
