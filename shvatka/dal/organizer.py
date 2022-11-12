from abc import ABCMeta
from typing import Iterable

from shvatka.dal.base import Reader, Committer
from shvatka.dal.game import GameByIdGetter
from shvatka.dal.secure_invite import InviteReader, InviteRemover
from shvatka.models import dto


class GameOrgsGetter(Reader):
    async def get_orgs(self, game: dto.Game) -> Iterable[dto.SecondaryOrganizer]:
        raise NotImplementedError


class OrgAdder(Committer, InviteReader, InviteRemover, GameByIdGetter, GameOrgsGetter, metaclass=ABCMeta):
    async def add_new_org(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        raise NotImplementedError
