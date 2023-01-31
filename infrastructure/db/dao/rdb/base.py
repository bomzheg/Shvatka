from typing import TypeVar, Type, Generic, Sequence

from sqlalchemy import delete, func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.strategy_options import Load

from infrastructure.db.models import Base

Model = TypeVar("Model", Base, Base)


class BaseDAO(Generic[Model]):
    def __init__(self, model: Type[Model], session: AsyncSession):
        self.model = model
        self.session = session

    async def _get_all(self) -> Sequence[Model]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def _get_by_id(self, id_: int, options: Sequence[Load] = None) -> Model:
        return await self.session.get(self.model, id_, options=options)

    def _save(self, obj: Model):
        self.session.add(obj)

    async def delete_all(self):
        await self.session.execute(delete(self.model))

    async def _delete(self, obj: Model):
        await self.session.delete(obj)

    async def count(self):
        result = await self.session.execute(select(func.count(self.model.id)))
        return result.scalar_one()

    async def commit(self):
        await self.session.commit()

    async def _flush(self, *objects):
        await self.session.flush(objects)
