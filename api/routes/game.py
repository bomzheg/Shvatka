from fastapi import APIRouter
from fastapi.params import Depends

from api.dependencies import dao_provider, player_provider, active_game_provider
from api.models import responses
from infrastructure.db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game import get_authors_games


async def get_my_games_list(
    player: dto.Player = Depends(player_provider),
    dao: HolderDao = Depends(dao_provider),
) -> list[dto.Game]:
    return await get_authors_games(player, dao.game)


async def get_active_game(game: dto.Game = Depends(active_game_provider)) -> responses.Game:
    return responses.Game.from_core(game)


def setup(router: APIRouter):
    router.add_api_route("/games/my", get_my_games_list, methods=["GET"])
    router.add_api_route("/games/active", get_active_game, methods=["GET"])
