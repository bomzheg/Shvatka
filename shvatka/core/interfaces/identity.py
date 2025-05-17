from typing import Protocol


from shvatka.core.models import dto
from shvatka.core.utils import exceptions


class IdentityProvider(Protocol):
    async def get_user(self) -> dto.User | None:
        raise NotImplementedError

    async def get_player(self) -> dto.Player | None:
        raise NotImplementedError

    async def get_chat(self) -> dto.Chat | None:
        raise NotImplementedError

    async def get_team(self) -> dto.Team | None:
        raise NotImplementedError

    async def get_required_user(self) -> dto.User:
        user = await self.get_user()
        if user is None:
            raise exceptions.PlayerNotFoundError
        return user

    async def get_required_player(self) -> dto.Player:
        player = await self.get_player()
        if player is None:
            raise exceptions.PlayerNotFoundError
        return player
