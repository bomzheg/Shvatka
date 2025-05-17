import pytest
import pytest_asyncio
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from httpx import AsyncClient

from shvatka.api.config.models.auth import AuthConfig
from shvatka.api.config.models.main import ApiConfig
from shvatka.api.main_factory import create_app
from shvatka.core.models import dto
from shvatka.core.services.user import upsert_user, set_password
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.api.dependencies.auth import AuthProperties
from tests.fixtures.identity import MockIdentityProvider
from tests.fixtures.user_constants import create_dto_harry


@pytest_asyncio.fixture(scope="session")
async def api_config(dishka: AsyncContainer) -> ApiConfig:
    return await dishka.get(ApiConfig)


@pytest.fixture(scope="session")
def app(dishka: AsyncContainer, api_config: ApiConfig):
    app = create_app(api_config)
    setup_dishka(dishka, app)
    return app


@pytest_asyncio.fixture(scope="session")
async def auth(dishka: AsyncContainer) -> AuthProperties:
    return AuthProperties(await dishka.get(AuthConfig))


@pytest.mark.anyio
@pytest_asyncio.fixture(scope="session")
async def client(app: FastAPI):
    async with (
        AsyncClient(app=app, base_url="http://test") as ac,
    ):
        yield ac


@pytest_asyncio.fixture
async def user(dao: HolderDao, auth: AuthProperties) -> dto.User:
    user_ = await upsert_user(create_dto_harry(), dao.user)
    password = auth.get_password_hash("12345")
    await set_password(MockIdentityProvider(user=user_), password, dao.user)
    return user_
