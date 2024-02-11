from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from shvatka.api.config.models.main import ApiConfig
from shvatka.api.config.parser.main import load_config
from shvatka.api.dependencies import AuthProvider
from shvatka.api.main_factory import create_app
from shvatka.common import Paths
from shvatka.core.models import dto
from shvatka.core.services.user import upsert_user, set_password
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.user_constants import create_dto_harry
from tests.integration.conftest import (
    event_loop,  # noqa: F401
    paths,  # noqa: F401
    pool,  # noqa: F401
    dao,  # noqa: F401
    postgres_url,  # noqa: F401
    redis,  # noqa: F401
    bot,  # noqa: F401
    bot_config,  # noqa: F401
    harry,  # noqa: F401
    hermione,  # noqa: F401
    ron,  # noqa: F401
    draco,  # noqa: F401
    gryffindor,  # noqa: F401
    slytherin,  # noqa: F401
    level_test_dao,  # noqa: F401
    file_storage,  # noqa: F401
    finished_game,  # noqa: F401
    game,  # noqa: F401
    complex_scn,  # noqa: F401
    file_gateway,  # noqa: F401
    fixtures_resource_path,  # noqa: F401
    author,  # noqa: F401
    session,  # noqa: F401
    alembic_config,  # noqa: F401
    upgrade_schema_db,  # noqa: F401
    dcf,  # noqa: F401
    game_log,  # noqa: F401
)
from tests.mocks.config import DBConfig


@pytest.fixture(scope="session")
def api_config(paths: Paths) -> ApiConfig:
    return load_config(paths)


@pytest.fixture(autouse=True)
def patch_api_config(api_config: ApiConfig, postgres_url: str, redis: Redis):
    api_config.db = DBConfig(postgres_url)  # type: ignore[assignment]
    api_config.redis.url = redis.connection_pool.connection_kwargs["host"]
    api_config.redis.port = redis.connection_pool.connection_kwargs["port"]
    api_config.redis.db = redis.connection_pool.connection_kwargs["db"]


@pytest.fixture(scope="session")
def app(api_config: ApiConfig, pool: async_sessionmaker[AsyncSession], redis: Redis) -> FastAPI:
    app = create_app(pool=pool, redis=redis, config=api_config)
    return app


@pytest.fixture(scope="session")
def auth(api_config: ApiConfig):
    return AuthProvider(api_config.auth)


@pytest.mark.anyio
@pytest_asyncio.fixture(scope="session")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def user(dao: HolderDao, auth: AuthProvider) -> dto.User:
    user_ = await upsert_user(create_dto_harry(), dao.user)
    password = auth.get_password_hash("12345")
    await set_password(user_, password, dao.user)
    return user_
