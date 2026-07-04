from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.player import (
    PlayerByIdGetter,
    PlayerByUserIdGetter,
    PlayerMerger,
)
from shvatka.core.interfaces.dal.user import UserUpserter
from shvatka.core.models import dto


class AdminEmailSetter(PlayerByIdGetter, Committer, Protocol):
    async def get_by_email(self, email: str) -> dto.EmailAccount | None:
        raise NotImplementedError

    async def set_player_email(
        self, player_id: int, email: str, is_verified: bool
    ) -> dto.EmailAccount:
        raise NotImplementedError


class AdminTgChanger(UserUpserter, PlayerByIdGetter, PlayerByUserIdGetter, Protocol):
    async def unlink_user(self, player: dto.Player) -> None:
        raise NotImplementedError

    async def link_user(self, player: dto.Player, user: dto.User) -> None:
        raise NotImplementedError


class AdminPlayerMerger(PlayerMerger, PlayerByIdGetter, Protocol):
    """Merge one player into another, plus load both by id."""
