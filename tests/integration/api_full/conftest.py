from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from api import dependencies, routes
from api.config.models.main import ApiConfig
from api.config.parser.main import load_config
from api.dependencies import AuthProvider
from api.main_factory import create_app
from common.config.models.paths import Paths
from tests.mocks.config import DBConfig


@pytest.fixture(scope="session")
def api_config(paths: Paths) -> ApiConfig:
    return load_config(paths)


@pytest.fixture(autouse=True)
def patch_api_config(api_config: ApiConfig, postgres_url: str, redis: Redis):
    api_config.db = DBConfig(postgres_url)  # type: ignore
    api_config.redis.url = redis.connection_pool.connection_kwargs["host"]
    api_config.redis.port = redis.connection_pool.connection_kwargs["port"]
    api_config.redis.db = redis.connection_pool.connection_kwargs["db"]


@pytest.fixture(scope="session")
def app(api_config: ApiConfig, pool: sessionmaker, redis: Redis) -> FastAPI:
    app = create_app()
    dependencies.setup(app=app, pool=pool, redis=redis, config=api_config)
    routes.setup(app.router)
    return app


@pytest.fixture(scope="session")
def auth(api_config: ApiConfig):
    return AuthProvider(api_config.auth)


@pytest.mark.anyio
@pytest_asyncio.fixture(scope="session")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
