from typing import Protocol

from shvatka.core.models import dto


class SuperusersResolver(Protocol):
    def is_superuser(self, user: dto.User) -> bool:
        raise NotImplementedError

    async def get_superuser_user_ids(self) -> set[int]:
        raise NotImplementedError

    async def get_superuser_player_ids(self) -> set[int]:
        raise NotImplementedError
