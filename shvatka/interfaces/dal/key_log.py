from abc import ABCMeta

from shvatka.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.models import dto


class TypedKeyGetter(OrgByPlayerGetter, metaclass=ABCMeta):
    async def get_typed_keys(self, game: dto.Game) -> list[dto.KeyTime]:
        raise NotImplementedError
