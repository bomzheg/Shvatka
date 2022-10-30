from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.models import User
from shvatka.models import dto
from shvatka.utils.exceptions import MultipleUsernameFound, NoUsernameFound
from .base import BaseDAO


class UserDao(BaseDAO[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_tg_id(self, tg_id: int) -> User:
        result = await self.session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        return result.scalar_one()

    async def get_by_username(self, username: str) -> dto.User:
        user = await self._get_by_username(username)
        return user.to_dto()

    async def get_by_username_with_password(self, username: str) -> dto.UserWithCreds:
        user = await self._get_by_username(username)
        return user.to_dto().add_password(user.hashed_password)

    async def _get_by_username(self, username: str) -> User:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        try:
            user = result.scalar_one()
        except MultipleResultsFound as e:
            raise MultipleUsernameFound(username=username) from e
        except NoResultFound as e:
            raise NoUsernameFound(username=username) from e
        return user

    async def set_password(self, user: dto.User, hashed_password: str):
        db_user = await self._get_by_id(user.db_id)
        db_user.hashed_password = hashed_password
        user.hashed_password = hashed_password

    async def upsert_user(self, user: dto.User) -> dto.User:
        try:
            saved_user = await self.get_by_tg_id(user.tg_id)
        except NoResultFound:
            saved_user = User(tg_id=user.tg_id)
        was_changed = update_fields(source=user, target=saved_user)
        if was_changed:
            self._save(saved_user)
            await self._flush(saved_user)
        return saved_user.to_dto()


def update_fields(target: User, source: dto.User) -> bool:
    if source.first_name is None:
        # this user is created from username only
        return False
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
