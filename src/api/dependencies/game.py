from fastapi.params import Depends

from src.infrastructure.db.dao.holder import HolderDao
from src.shvatka.services.game import get_active
from .db import dao_provider
from ...shvatka.models import dto


def active_game_provider() -> dto.Game:
    raise NotImplementedError


async def db_game_provider(
    dao: HolderDao = Depends(dao_provider),  # type: ignore[assignment]
) -> dto.Game:
    return await get_active(dao.game)
