from abc import ABCMeta

from shvatka.dal.base import Committer
from shvatka.models import dto


class UserUpserter(Committer, metaclass=ABCMeta):
    async def upsert_user(self, user: dto.User) -> dto.User:
        raise NotImplementedError
