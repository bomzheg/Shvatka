from abc import ABCMeta

from shvatka.interfaces.dal.base import Writer, Reader


class InviteSaver(Writer):
    async def save_new_invite(self, token_len: int = ..., expire=..., **dct: dict) -> str:
        raise NotImplementedError


class InviteRemover(Writer):
    async def remove_invite(self, token: str) -> None:
        raise NotImplementedError


class InviteReader(Reader):
    async def get_invite(self, token: str) -> dict:
        raise NotImplementedError


class InviterDao(InviteSaver, InviteRemover, InviteReader, metaclass=ABCMeta):
    pass
