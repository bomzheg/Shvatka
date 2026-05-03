from shvatka.core.interfaces.dal.user import UserUpserter, UserByIdResolver
from shvatka.core.models import dto


async def upsert_user(user: dto.User, user_dao: UserUpserter) -> dto.User:
    saved_user = await user_dao.upsert_user(user)
    await user_dao.commit()
    return saved_user


async def get_user(id_: int, dao: UserByIdResolver):
    return await dao.get_by_id(id_)
