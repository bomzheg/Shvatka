from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models import dto


class UserPasswordSetter(Committer, Protocol):
    async def set_password(self, user: dto.Player, hashed_password: str):
        raise NotImplementedError


class PlayerUsernameChanger(Committer, Protocol):
    async def is_username_occupied(self, username: str) -> bool:
        raise NotImplementedError

    async def set_username(self, player: dto.Player, username: str) -> None:
        raise NotImplementedError
