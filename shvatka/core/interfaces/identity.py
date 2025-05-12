from typing import Protocol

from shvatka.core.models import dto


class IdentityProvider(Protocol):
    async def get_user(self) -> dto.User:
        raise NotImplementedError

    async def get_player(self) -> dto.Player:
        raise NotImplementedError

    async def get_chat(self) -> dto.Chat:
        raise NotImplementedError

    async def get_team(self) -> dto.Team:
        raise NotImplementedError
