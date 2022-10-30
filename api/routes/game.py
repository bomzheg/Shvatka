from fastapi import APIRouter
from fastapi.params import Depends

from api.dependencies import dao_provider, player_provider
from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game import get_authors_games


async def get_my_games_list(
    player: dto.Player = Depends(player_provider),
    dao: HolderDao = Depends(dao_provider),
) -> list[dto.Game]:
    return await get_authors_games(player, dao.game)


def setup(router: APIRouter):
    router.add_api_route("/games/my", get_my_games_list, methods=["GET"])
