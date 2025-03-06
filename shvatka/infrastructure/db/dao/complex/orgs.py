import typing
from dataclasses import dataclass

from shvatka.core.interfaces.dal.organizer import OrgAdder
from shvatka.core.models import dto

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class OrgAdderImpl(OrgAdder):
    dao: "HolderDao"

    async def add_new_org(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return await self.dao.organizer.add_new(game, player)

    async def commit(self) -> None:
        await self.dao.commit()

    async def get_invite(self, token: str) -> dict:
        return await self.dao.secure_invite.get_invite(token)

    async def remove_invite(self, token: str) -> None:
        return await self.dao.secure_invite.remove_invite(token)

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_=id_, author=author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_=id_)

    async def get_orgs(
        self, game: dto.Game, with_deleted: bool = False
    ) -> list[dto.SecondaryOrganizer]:
        return await self.dao.organizer.get_orgs(game)

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        return await self.dao.game.add_levels(game)
