from shvatka.dal.user import UserUpserter, UserPasswordSetter
from shvatka.models import dto


async def upsert_user(user: dto.User, user_dao: UserUpserter) -> dto.User:
    saved_user = await user_dao.upsert_user(user)
    await user_dao.commit()
    return saved_user


async def set_password(user: dto.User, hashed_password: str, dao: UserPasswordSetter):
    await dao.set_password(user, hashed_password)
    await dao.commit()
