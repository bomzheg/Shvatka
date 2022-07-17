from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.dao.base import BaseDAO
from app.models.db import User
from app.models import dto


class UserDao(BaseDAO[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_tg_id(self, tg_id: int) -> User:
        result = await self.session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        return result.scalar_one()

    async def upsert_user(self, user: dto.User) -> dto.User:
        try:
            saved_user = await self.get_by_tg_id(user.tg_id)
        except NoResultFound:
            saved_user = User(tg_id=user.tg_id)
        was_changed = update_fields(source=user, target=saved_user)
        if was_changed:
            self.save(saved_user)
            await self.flush(saved_user)
        return dto.User.from_db(saved_user)


def update_fields(target: User, source: dto.User) -> bool:
    if all([
        target.first_name == source.first_name,
        target.last_name == source.last_name,
        target.username == source.username,
        target.is_bot == source.is_bot,
    ]):
        return False
    target.first_name = source.first_name
    target.last_name = source.last_name
    target.username = source.username
    target.is_bot = source.is_bot
    return True
