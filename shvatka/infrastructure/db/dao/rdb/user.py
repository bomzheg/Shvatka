from datetime import datetime, tzinfo
import typing
from typing import Sequence

from sqlalchemy import select, ScalarResult, Result
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.models import dto
from shvatka.core.utils import exceptions
from shvatka.core.utils.exceptions import MultipleUsernameFound, NoUsernameFound
from shvatka.infrastructure.db.models import User
from .base import BaseDAO


class UserDao(BaseDAO[User]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(User, session, clock=clock)

    async def get_by_id(self, id_: int) -> dto.User:
        return (await self._get_by_id(id_)).to_dto()

    async def get_by_tg_id(self, tg_id: int) -> dto.User:
        return (await self._get_by_tg_id(tg_id)).to_dto()

    async def _get_by_tg_id(self, tg_id: int) -> User:
        result: ScalarResult[User] = await self.session.scalars(
            select(User).where(User.tg_id == tg_id)
        )
        try:
            return result.one()
        except NoResultFound as e:
            raise exceptions.UserNotFoundError(user_id=tg_id) from e

    async def get_by_username(self, username: str) -> dto.User:
        user = await self._get_by_username(username)
        return user.to_dto()

    async def get_by_username_with_password(self, username: str) -> dto.UserWithCreds:
        user = await self._get_by_username(username)
        return user.to_dto().add_password(user.hashed_password)

    async def _get_by_username(self, username: str) -> User:
        result: Result[tuple[User]] = await self.session.execute(
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
        assert user.db_id
        db_user = await self._get_by_id(user.db_id)
        db_user.hashed_password = hashed_password

    async def upsert_user(self, user: dto.User) -> dto.User:
        kwargs = {
            "tg_id": user.tg_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "is_bot": user.is_bot,
        }
        saved_user = await self.session.execute(
            insert(User)
            .values(**kwargs)
            .on_conflict_do_update(
                index_elements=(User.tg_id,), set_=kwargs, where=User.tg_id == user.tg_id
            )
            .returning(User)
        )
        return saved_user.scalar_one().to_dto()

    async def get_page(self, offset: int, limit: int) -> Sequence[dto.User]:
        result: ScalarResult[User] = await self.session.scalars(
            select(User).offset(offset).limit(limit)
        )
        return [user.to_dto() for user in result.all()]
