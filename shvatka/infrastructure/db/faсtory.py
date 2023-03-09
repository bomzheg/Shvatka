import logging

from redis.asyncio import Redis
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine

from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.db.config.models.db import DBConfig, RedisConfig
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.db.dao.memory.locker import MemoryLockFactory

logger = logging.getLogger(__name__)


def create_pool(db_config: DBConfig) -> async_sessionmaker[AsyncSession]:
    engine = create_engine(db_config)
    return create_session_maker(engine)


def create_engine(db_config: DBConfig) -> AsyncEngine:
    return create_async_engine(url=make_url(db_config.uri), echo=db_config.echo)


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    pool: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False
    )
    return pool


def create_lock_factory() -> KeyCheckerFactory:
    return MemoryLockFactory()


def create_redis(config: RedisConfig) -> Redis:
    logger.info("created redis for %s", config)
    return Redis(host=config.url, port=config.port, db=config.db)


def create_level_test_dao():
    level_test_dao = LevelTestingData()
    return level_test_dao
