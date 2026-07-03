from typing import Any

from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.players.player import get_player_with_stat, get_teams_history
from shvatka.core.services.one_time_link import GenerateOneTimeLoginLinkInteractor
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
    interactor: FromDishka[GenerateOneTimeLoginLinkInteractor],
    identity: FromDishka[IdentityProvider],
    **_,
) -> dict[str, Any]:
    return {
        "player": await identity.get_required_player(),
        "url": await interactor(identity=identity),
    }
