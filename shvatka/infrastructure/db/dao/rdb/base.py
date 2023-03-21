from typing import TypeVar, Type, Generic, Sequence

from sqlalchemy import delete, func, ScalarResult
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ORMOption

from shvatka.infrastructure.db.models import Base

Model = TypeVar("Model", bound=Base, covariant=True, contravariant=False)


class BaseDAO(Generic[Model]):
    def __init__(self, model: Type[Model], session: AsyncSession):
        self.model = model
        self.session = session

    async def _get_all(self, options: Sequence[ORMOption] = tuple()) -> Sequence[Model]:
        result: ScalarResult[Model] = await self.session.scalars(
            select(self.model).options(*options)
        )
        return result.all()

    async def _get_by_id(
        self, id_: int, options: Sequence[ORMOption] = None, populate_existing: bool = False
    ) -> Model:
        result = await self.session.get(
            self.model, id_, options=options, populate_existing=populate_existing
        )
        if result is None:
            raise NoResultFound()
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
