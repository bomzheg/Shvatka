from typing import Protocol

from shvatka.interfaces.dal.base import Committer
from shvatka.interfaces.dal.game import GameByIdGetter
from shvatka.interfaces.dal.secure_invite import InviteReader, InviteRemover
from shvatka.models import dto
from shvatka.models.enums.org_permission import OrgPermission


class GameOrgsGetter(Protocol):
    async def get_orgs(
        self, game: dto.Game, with_deleted: bool = False
    ) -> list[dto.SecondaryOrganizer]:
        raise NotImplementedError


class OrgAdder(
    Protocol, Committer, InviteReader, InviteRemover, GameByIdGetter, GameOrgsGetter
):
    async def add_new_org(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        raise NotImplementedError


class OrgByIdGetter(Protocol):
    async def get_by_id(self, id_: int) -> dto.SecondaryOrganizer:
        raise NotImplementedError


class OrgByPlayerGetter(Protocol):
    async def get_by_player(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        raise NotImplementedError

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        raise NotImplementedError


class OrgPermissionFlipper(Protocol, Committer, OrgByIdGetter):
    async def flip_permission(self, org: dto.SecondaryOrganizer, permission: OrgPermission):
        raise NotImplementedError


class OrgDeletedFlipper(Protocol, Committer, OrgByIdGetter):
    async def flip_deleted(self, org: dto.SecondaryOrganizer):
        raise NotImplementedError
