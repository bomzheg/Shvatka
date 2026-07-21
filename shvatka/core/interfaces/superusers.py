from typing import Protocol

from shvatka.core.models import dto


class SuperusersResolver(Protocol):
    """Single source of truth for who the configured superusers (admins) are.

    Exposes the same set of superusers as tg ids, as player ids, and as a
    membership check, so every edge (api auth, bot, notifications) resolves
    admin rights the same way instead of re-reading the config on its own.
    """

    def is_superuser(self, user: dto.User) -> bool:
        raise NotImplementedError

    async def get_superuser_user_ids(self) -> set[int]:
        raise NotImplementedError

    async def get_superuser_player_ids(self) -> set[int]:
        raise NotImplementedError
