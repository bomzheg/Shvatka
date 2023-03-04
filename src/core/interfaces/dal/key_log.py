from typing import Protocol

from src.core.interfaces.dal.organizer import OrgByPlayerGetter
from src.core.models import dto


class TypedKeyGetter(OrgByPlayerGetter, Protocol):
    async def get_typed_keys(self, game: dto.Game) -> list[dto.KeyTime]:
        raise NotImplementedError
