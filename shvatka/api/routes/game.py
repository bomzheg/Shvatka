from fastapi import APIRouter
from fastapi.params import Depends

from shvatka.api.dependencies import dao_provider, player_provider, active_game_provider
from shvatka.api.models import responses
from shvatka.core.models import dto
from shvatka.core.services.game import get_authors_games
from shvatka.infrastructure.db.dao.holder import HolderDao


async def get_my_games_list(
    player: dto.Player = Depends(player_provider),  # type: ignore[assignment]
    dao: HolderDao = Depends(dao_provider),  # type: ignore[assignment]
):
    return await get_authors_games(player, dao.game)


async def get_active_game(
    game: dto.Game = Depends(active_game_provider),  # type: ignore[assignment]
) -> responses.Game | None:
    return responses.Game.from_core(game)


def setup() -> APIRouter:
    router = APIRouter(prefix="/games")
    router.add_api_route("/my", get_my_games_list, methods=["GET"])
    router.add_api_route("/active", get_active_game, methods=["GET"])
    return router
