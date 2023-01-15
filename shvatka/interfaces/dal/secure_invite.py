from typing import Protocol


class InviteSaver(Protocol):
    async def save_new_invite(self, token_len: int = ..., expire=..., **dct: dict) -> str:
        raise NotImplementedError


class InviteRemover(Protocol):
    async def remove_invite(self, token: str) -> None:
        raise NotImplementedError


class InviteReader(Protocol):
    async def get_invite(self, token: str) -> dict:
        raise NotImplementedError


class InviterDao(InviteSaver, InviteRemover, InviteReader, Protocol):
    pass
