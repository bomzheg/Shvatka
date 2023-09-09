from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData


def dao_provider() -> HolderDao:
    raise NotImplementedError


class DbProvider:
    def __init__(self, pool: async_sessionmaker[AsyncSession], redis: Redis) -> None:
        self.pool = pool
        self.redis = redis
        self.level_test = LevelTestingData()

    async def dao(self):
        async with self.pool() as session:
            yield HolderDao(session=session, redis=self.redis, level_test=self.level_test)
