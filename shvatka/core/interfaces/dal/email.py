import typing

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models import dto


class EmailAccountDao(typing.Protocol):
    async def get_by_email(self, email: str) -> dto.EmailAccount | None:
        raise NotImplementedError

    async def get_by_player_id(self, player_id: int) -> dto.EmailAccount | None:
        raise NotImplementedError

    async def is_email_occupied(self, email: str) -> bool:
        raise NotImplementedError

    async def create_player_for_email(
        self, username: str, email: str, hashed_password: str
    ) -> dto.Player:
        raise NotImplementedError

    async def add_email_to_player(self, player: dto.Player, email: str) -> dto.EmailAccount:
        raise NotImplementedError

    async def set_player_email(
        self, player_id: int, email: str, is_verified: bool
    ) -> dto.EmailAccount:
        raise NotImplementedError

    async def set_verified(self, email: str) -> None:
        raise NotImplementedError

    async def find_verified_player_by_email(self, email: str) -> dto.Player:
        raise NotImplementedError


class UsernameOccupiedChecker(typing.Protocol):
    async def is_username_occupied(self, username: str) -> bool:
        raise NotImplementedError


class EmailConfirmationStore(typing.Protocol):
    async def save_code(self, email: str, code: str, player_id: int) -> None:
        raise NotImplementedError

    async def get_code(self, email: str) -> dto.EmailConfirmation | None:
        raise NotImplementedError

    async def remove_code(self, email: str) -> None:
        raise NotImplementedError

    async def get_pending_email(self, player_id: int) -> str | None:
        """The email a player is currently asked to confirm, if any."""
        raise NotImplementedError


class EmailDao(EmailAccountDao, Committer, typing.Protocol):
    pass
