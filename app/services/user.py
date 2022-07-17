from app.dao import UserDao
from app.models import dto


async def upsert_user(user: dto.User, user_dao: UserDao) -> dto.User:
    saved_user = await user_dao.upsert_user(user)
    await user_dao.commit()
    return saved_user
