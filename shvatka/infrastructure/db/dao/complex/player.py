import typing
from dataclasses import dataclass

from shvatka.core.interfaces.dal.player import PlayerPromoter, PlayerMerger
from shvatka.core.models import dto

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class PlayerPromoterImpl(PlayerPromoter):
    dao: "HolderDao"

    async def promote(self, actor: dto.Player, target: dto.Player) -> None:
        return await self.dao.player.promote(actor, target)

    async def get_by_id(self, id_: int) -> dto.Player:
        return await self.dao.player.get_by_id(id_)

    async def commit(self) -> None:
        return await self.dao.player.commit()

    async def get_invite(self, token: str) -> dict:
        return await self.dao.secure_invite.get_invite(token)

    async def remove_invite(self, token: str) -> None:
        return await self.dao.secure_invite.remove_invite(token)


@dataclass
class PlayerMergerImpl(PlayerMerger):
    dao: "HolderDao"
