from typing import TypeVar, Generic
from collections.abc import Sequence

from sqlalchemy import delete, func, ScalarResult
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ORMOption

from shvatka.infrastructure.db.models import Base

Model_co = TypeVar("Model_co", bound=Base, covariant=True, contravariant=False)


class BaseDAO(Generic[Model_co]):
    def __init__(self, model: type[Model_co], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def _get_all(self, options: Sequence[ORMOption] = ()) -> Sequence[Model_co]:
        result: ScalarResult[Model_co] = await self.session.scalars(
            select(self.model).options(*options)
        )
        return result.all()

    async def _get_by_id(
        self, id_: int, options: Sequence[ORMOption] | None = None, populate_existing: bool = False
    ) -> Model_co:
        result = await self.session.get(
            self.model, id_, options=options, populate_existing=populate_existing
        )
        if result is None:
            raise NoResultFound
        return result

    def _save(self, obj: Base):
        self.session.add(obj)

    async def delete_all(self):
        await self.session.execute(delete(self.model))

    async def _delete(self, obj: Base):
        await self.session.delete(obj)

    async def count(self):
        result = await self.session.execute(select(func.count(self.model.id)))
        return result.scalar_one()

    async def commit(self):
        await self.session.commit()

    async def _flush(self, *objects: Base):
        await self.session.flush(objects)
