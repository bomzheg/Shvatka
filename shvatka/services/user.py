from shvatka.dal.user import UserUpserter
from shvatka.models import dto


async def upsert_user(user: dto.User, user_dao: UserUpserter) -> dto.User:
    saved_user = await user_dao.upsert_user(user)
    await user_dao.commit()
    return saved_user
