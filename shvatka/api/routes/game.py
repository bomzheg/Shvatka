from fastapi import APIRouter
from fastapi.params import Depends, Path

from shvatka.api.dependencies import dao_provider, player_provider, active_game_provider
from shvatka.api.models import responses
from shvatka.core.models import dto
from shvatka.core.services.game import get_authors_games, get_completed_games, get_full_game
from shvatka.infrastructure.db.dao.holder import HolderDao


async def get_my_games_list(
    player: dto.Player = Depends(player_provider),  # type: ignore[assignment]
    dao: HolderDao = Depends(dao_provider),  # type: ignore[assignment]
):
    return responses.Page(await get_authors_games(player, dao.game))


async def get_active_game(
    game: dto.Game = Depends(active_game_provider),  # type: ignore[assignment]
) -> responses.Game | None:
    return responses.Game.from_core(game)


async def get_all_games(
    dao: HolderDao = Depends(dao_provider),  # type: ignore[assignment]
) -> responses.Page[responses.Game]:
    games = await get_completed_games(dao.game)
    return responses.Page([responses.Game.from_core(game) for game in games])


async def get_game_card(
    dao: HolderDao = Depends(dao_provider),  # type: ignore[assignment]
    player: dto.Player = Depends(player_provider),  # type: ignore[assignment]
    id_: int = Path(alias="id"),  # type: ignore[assignment]
):
    game = await get_full_game(id_, player, dao.game)
    return responses.FullGame.from_core(game)


def setup() -> APIRouter:
    router = APIRouter(prefix="/games")
    router.add_api_route("", get_all_games, methods=["GET"])
    router.add_api_route("/my", get_my_games_list, methods=["GET"])
    router.add_api_route("/active", get_active_game, methods=["GET"])
    router.add_api_route("/{id}", get_game_card, methods=["GET"])
    return router
