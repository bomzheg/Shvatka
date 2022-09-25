from shvatka.dal.base import Committer
from shvatka.models import dto


class UserUpserter(Committer):
    async def upsert_user(self, user: dto.User) -> dto.User: pass
