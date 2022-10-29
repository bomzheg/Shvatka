import logging
import os
from pathlib import Path

from fastapi import FastAPI
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from api.config.models.main import Paths
from db.config.models.db import RedisConfig
from scheduler import ApScheduler
from shvatka.scheduler import Scheduler

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
