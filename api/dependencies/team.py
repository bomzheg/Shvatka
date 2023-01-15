from fastapi.params import Depends

from api.dependencies import dao_provider, player_provider
from infrastructure.db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import get_my_team
from shvatka.utils import exceptions


def team_provider() -> dto.Team:
    raise NotImplementedError


async def db_team_provider(
    dao: HolderDao = Depends(dao_provider),  # type: ignore[assignment]
    player: dto.Player = Depends(player_provider),  # type: ignore[assignment]
) -> dto.Team:
    team = await get_my_team(player, dao.team_player)
    if team is None:
        raise exceptions.PlayerNotInTeam()
    return team
