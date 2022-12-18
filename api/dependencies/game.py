from fastapi.params import Depends

from infrastructure.db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game import get_active
from .db import dao_provider


def active_game_provider():
    raise NotImplementedError


async def db_game_provider(
    dao: HolderDao = Depends(dao_provider),
) -> dto.Game:
    return await get_active(dao.game)
