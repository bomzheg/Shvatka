from fastapi.params import Depends

from src.api.dependencies import dao_provider, player_provider
from src.infrastructure.db.dao.holder import HolderDao
from src.core.models import dto
from src.core.services.player import get_my_team
from src.core.utils import exceptions


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
