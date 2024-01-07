import logging

from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from shvatka.api import dependencies, routes
from shvatka.api.config.models.main import ApiConfig
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.paths import common_get_paths

logger = logging.getLogger(__name__)


def create_app(pool: async_sessionmaker[AsyncSession], redis: Redis, config: ApiConfig) -> FastAPI:
    app = FastAPI()
    dependencies.setup(app=app, pool=pool, redis=redis, config=config)
    app.include_router(routes.setup())
    return app


def get_paths() -> Paths:
    return common_get_paths("API_PATH")
