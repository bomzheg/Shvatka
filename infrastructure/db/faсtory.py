import logging

from redis.asyncio import Redis
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from infrastructure.db.config.models.db import DBConfig, RedisConfig
from infrastructure.db.dao.memory.locker import MemoryLockFactory
from shvatka.utils.key_checker_lock import KeyCheckerFactory

logger = logging.getLogger(__name__)


def create_pool(db_config: DBConfig) -> sessionmaker:
    engine = create_async_engine(url=make_url(db_config.uri), echo=db_config.echo)
    pool = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    return pool


def create_lock_factory() -> KeyCheckerFactory:
    return MemoryLockFactory()


def create_redis(config: RedisConfig) -> Redis:
    logger.info("created redis for %s", config)
    return Redis(host=config.url, port=config.port, db=config.db)
