from typing import Protocol

from src.shvatka.interfaces.dal.base import Committer
from src.shvatka.interfaces.dal.game import GameByIdGetter
from src.shvatka.interfaces.dal.secure_invite import InviteReader, InviteRemover
from src.shvatka.models import dto
from src.shvatka.models.enums.org_permission import OrgPermission


class GameOrgsGetter(Protocol):
    async def get_orgs(
        self, game: dto.Game, with_deleted: bool = False
    ) -> list[dto.SecondaryOrganizer]:
        raise NotImplementedError


class OrgAdder(Committer, InviteReader, InviteRemover, GameByIdGetter, GameOrgsGetter, Protocol):
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


class OrgPermissionFlipper(Committer, OrgByIdGetter, Protocol):
    async def flip_permission(self, org: dto.SecondaryOrganizer, permission: OrgPermission):
        raise NotImplementedError


class OrgDeletedFlipper(Committer, OrgByIdGetter, Protocol):
    async def flip_deleted(self, org: dto.SecondaryOrganizer):
        raise NotImplementedError
