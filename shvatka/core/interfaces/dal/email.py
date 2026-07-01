import typing

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models import dto


class EmailAccountDao(typing.Protocol):
    async def get_by_email(self, email: str) -> dto.EmailAccount | None:
        ...

    async def is_email_occupied(self, email: str) -> bool:
        ...

    async def create_player_for_email(self, email: str, hashed_password: str) -> dto.Player:
        ...

    async def add_email_to_player(self, player: dto.Player, email: str) -> dto.EmailAccount:
        ...

    async def set_verified(self, email: str) -> None:
        ...

    async def set_password_if_absent(self, player: dto.Player, hashed_password: str) -> None:
        ...


class EmailConfirmationStore(typing.Protocol):
    async def save_code(self, email: str, code: str, player_id: int) -> None:
        ...

    async def get_code(self, email: str) -> dto.EmailConfirmation | None:
        ...

    async def remove_code(self, email: str) -> None:
        ...


class EmailRegistrar(EmailAccountDao, Committer, typing.Protocol):
    ...


class EmailConfirmer(EmailAccountDao, Committer, typing.Protocol):
    ...
