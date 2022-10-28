import logging
import os
from pathlib import Path

from fastapi import FastAPI
from redis.asyncio.client import Redis
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from api.config.models.main import Paths
from db.config.models.db import RedisConfig, DBConfig
from db.locker import MemoryLockFactory
from scheduler import ApScheduler
from shvatka.scheduler import Scheduler
from shvatka.utils.key_checker_lock import KeyCheckerFactory

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    return FastAPI()


def create_scheduler(
    pool: sessionmaker, redis: Redis, redis_config: RedisConfig,
) -> Scheduler:
    return ApScheduler(
        redis_config=redis_config, pool=pool, redis=redis,
    )


def get_paths() -> Paths:
    if path := os.getenv("API_PATH"):
        return Paths(Path(path))
    return Paths(Path(__file__).parent.parent)


def create_pool(db_config: DBConfig) -> sessionmaker:
    engine = create_async_engine(url=make_url(db_config.uri), echo=True)
    pool = sessionmaker(bind=engine, class_=AsyncSession,
                        expire_on_commit=False, autoflush=False)
    return pool


def create_lock_factory() -> KeyCheckerFactory:
    return MemoryLockFactory()


def create_redis(config: RedisConfig) -> Redis:
    logger.info("created redis for %s", config)
    return Redis(host=config.url, port=config.port, db=config.db)
