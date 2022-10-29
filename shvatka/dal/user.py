from abc import ABCMeta

from shvatka.dal.base import Committer, Reader
from shvatka.models import dto


class UserUpserter(Committer, metaclass=ABCMeta):
    async def upsert_user(self, user: dto.User) -> dto.User:
        raise NotImplementedError


class UserByUsernameResolver(Reader, metaclass=ABCMeta):
    async def get_by_username(self, username: str) -> dto.User:
        pass
