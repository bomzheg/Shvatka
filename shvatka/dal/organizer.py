from abc import ABCMeta

from shvatka.dal.base import Reader, Committer
from shvatka.dal.game import GameByIdGetter
from shvatka.dal.secure_invite import InviteReader, InviteRemover
from shvatka.models import dto
from shvatka.models.enums.org_permission import OrgPermission


class GameOrgsGetter(Reader):
    async def get_orgs(self, game: dto.Game, with_deleted: bool = False) -> list[dto.SecondaryOrganizer]:
        raise NotImplementedError


class OrgAdder(Committer, InviteReader, InviteRemover, GameByIdGetter, GameOrgsGetter, metaclass=ABCMeta):
    async def add_new_org(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        raise NotImplementedError


class OrgByIdGetter(Reader):
    async def get_by_id(self, id_: int) -> dto.SecondaryOrganizer:
        raise NotImplementedError


class OrgPermissionFlipper(Committer, OrgByIdGetter, metaclass=ABCMeta):
    async def flip_permission(self, org: dto.SecondaryOrganizer, permission: OrgPermission):
        raise NotImplementedError


class OrgDeletedFlipper(Committer, OrgByIdGetter, metaclass=ABCMeta):
    async def flip_deleted(self, org: dto.SecondaryOrganizer):
        raise NotImplementedError
