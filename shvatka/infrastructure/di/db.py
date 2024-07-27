from typing import AsyncIterable

from dishka import Provider, Scope, provide
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine

from shvatka.infrastructure.db.config.models.db import DBConfig, RedisConfig
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.db.factory import create_engine, create_session_maker, create_redis


class DbProvider(Provider):
    scope = Scope.APP

    def __init__(self):
        super().__init__()
        self.level_test = LevelTestingData()

    @provide
    async def get_engine(self, db_config: DBConfig) -> AsyncIterable[AsyncEngine]:
        engine = create_engine(db_config)
        yield engine
        await engine.dispose(True)

    @provide
    def get_pool(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return create_session_maker(engine)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, pool: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        async with pool() as session:
            yield session

    @provide
    def get_level_test_data(self) -> LevelTestingData:
        return self.level_test


class DAOProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_dao(
        self, session: AsyncSession, redis: Redis, level_test: LevelTestingData
    ) -> HolderDao:
        return HolderDao(session=session, redis=redis, level_test=level_test)


class RedisProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_redis(self, config: RedisConfig) -> AsyncIterable[Redis]:
        async with create_redis(config) as redis:
            yield redis
