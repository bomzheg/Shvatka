from dataclasses import dataclass

from infrastructure.db.dao import GameDao, OrganizerDao, SecureInvite
from shvatka.interfaces.dal.organizer import OrgAdder
from shvatka.models import dto


@dataclass
class OrgAdderImpl(OrgAdder):
    game: GameDao
    organizer: OrganizerDao
    secure_invite: SecureInvite

    async def add_new_org(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return await self.organizer.add_new(game, player)

    async def commit(self) -> None:
        await self.game.commit()

    async def get_invite(self, token: str) -> dict:
        return await self.secure_invite.get_invite(token)

    async def remove_invite(self, token: str) -> None:
        return await self.secure_invite.remove_invite(token)

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.game.get_by_id(id_=id_, author=author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.game.get_full(id_=id_)

    async def get_orgs(
        self, game: dto.Game, with_deleted: bool = False
    ) -> list[dto.SecondaryOrganizer]:
        return await self.organizer.get_orgs(game)
