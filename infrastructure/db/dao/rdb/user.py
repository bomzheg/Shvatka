from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models import User
from shvatka.models import dto
from shvatka.utils.exceptions import MultipleUsernameFound, NoUsernameFound
from .base import BaseDAO


class UserDao(BaseDAO[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_id(self, id_: int) -> dto.User:
        return (await self._get_by_id(id_)).to_dto()

    async def _get_by_tg_id(self, tg_id: int) -> User:
        result = await self.session.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar_one()

    async def get_by_username(self, username: str) -> dto.User:
        user = await self._get_by_username(username)
        return user.to_dto()

    async def get_by_username_with_password(self, username: str) -> dto.UserWithCreds:
        user = await self._get_by_username(username)
        return user.to_dto().add_password(user.hashed_password)

    async def _get_by_username(self, username: str) -> User:
        result = await self.session.execute(select(User).where(User.username == username))
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
        kwargs = dict(
            tg_id=user.tg_id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            is_bot=user.is_bot,
        )
        saved_user = await self.session.execute(
            insert(User)
            .values(**kwargs)
            .on_conflict_do_update(
                index_elements=(User.tg_id,), set_=kwargs, where=User.tg_id == user.tg_id
            )
            .returning(User)
        )
        return saved_user.scalar_one().to_dto()
