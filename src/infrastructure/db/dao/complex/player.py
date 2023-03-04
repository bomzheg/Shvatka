from dataclasses import dataclass

from src.infrastructure.db.dao import PlayerDao, SecureInvite
from src.shvatka.interfaces.dal.player import PlayerPromoter
from src.shvatka.models import dto


@dataclass
class PlayerPromoterImpl(PlayerPromoter):
    player: PlayerDao
    secure_invite: SecureInvite

    async def promote(self, actor: dto.Player, target: dto.Player) -> None:
        return await self.player.promote(actor, target)

    async def get_by_id(self, id_: int) -> dto.Player:
        return await self.player.get_by_id(id_)

    async def commit(self) -> None:
        return await self.player.commit()

    async def get_invite(self, token: str) -> dict:
        return await self.secure_invite.get_invite(token)

    async def remove_invite(self, token: str) -> None:
        return await self.secure_invite.remove_invite(token)
