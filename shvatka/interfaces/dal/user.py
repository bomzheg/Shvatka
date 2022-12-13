from abc import ABCMeta

from shvatka.interfaces.dal.base import Committer, Reader
from shvatka.models import dto


class UserUpserter(Committer, metaclass=ABCMeta):
    async def upsert_user(self, user: dto.User) -> dto.User:
        raise NotImplementedError


class UserPasswordSetter(Committer, metaclass=ABCMeta):
    async def set_password(self, user: dto.User, hashed_password: str):
        raise NotImplementedError


class UserByUsernameResolver(Reader, metaclass=ABCMeta):
    async def get_by_username(self, username: str) -> dto.User:
        raise NotImplementedError


class UserByIdResolver(Reader, metaclass=ABCMeta):
    async def get_by_id(self, id_: int) -> dto.User:
        raise NotImplementedError
