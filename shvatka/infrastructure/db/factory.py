import logging
from typing import Any

from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.db.config.models.db import DBConfig, RedisConfig
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.db.dao.memory.locker import MemoryLockFactory
from shvatka.infrastructure.db.metrics import instrument_pool

logger = logging.getLogger(__name__)


def create_pool(db_config: DBConfig) -> async_sessionmaker[AsyncSession]:
    engine = create_engine(db_config)
    return create_session_maker(engine)


def create_engine(db_config: DBConfig) -> AsyncEngine:
    url = make_url(db_config.uri)
    engine = create_async_engine(url=url, echo=db_config.echo, **pool_options(db_config, url))
    instrument_pool(engine)
    return engine


def pool_options(db_config: DBConfig, url: URL) -> dict[str, Any]:
    if url.get_backend_name() == "sqlite":
        return {}
    return {
        "pool_size": db_config.pool_size,
        "max_overflow": db_config.max_overflow,
        "pool_timeout": db_config.pool_timeout,
        "pool_recycle": db_config.pool_recycle,
        "pool_pre_ping": db_config.pool_pre_ping,
    }


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    pool: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False
    )
    return pool


def create_redis(config: RedisConfig) -> Redis:
    logger.info("created redis for %s", config)
    return Redis(host=config.url, port=config.port, db=config.db)


def create_level_test_dao():
    return LevelTestingData()


class LockProvider(Provider):
    scope = Scope.APP

    @provide
    def get_lock_factory(self) -> KeyCheckerFactory:
        return MemoryLockFactory()
