from fastapi.params import Depends

from api.dependencies import dao_provider, player_provider
from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import get_my_team


def team_provider():
    raise NotImplementedError


async def db_team_provider(
    dao: HolderDao = Depends(dao_provider),
    player: dto.Player = Depends(player_provider),
) -> dto.Team:
    return await get_my_team(player, dao.team_player)
