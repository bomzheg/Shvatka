from fastapi.params import Depends

from shvatka.core.services.game import get_active
from shvatka.infrastructure.db.dao.holder import HolderDao
from .db import dao_provider
from ...core.models import dto


def active_game_provider() -> dto.Game:
    raise NotImplementedError


async def db_game_provider(
    dao: HolderDao = Depends(dao_provider),  # type: ignore[assignment]
) -> dto.Game:
    return await get_active(dao.game)
