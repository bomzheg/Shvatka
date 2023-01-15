from typing import Protocol

from shvatka.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.models import dto


class TypedKeyGetter(OrgByPlayerGetter, Protocol):
    async def get_typed_keys(self, game: dto.Game) -> list[dto.KeyTime]:
        raise NotImplementedError
