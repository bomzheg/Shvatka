from asgi_lifespan import LifespanManager
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
from tests.fixtures.user_constants import create_dto_harry
from tests.integration.conftest import (
    event_loop,  # noqa: F401
    paths,  # noqa: F401
    dao,  # noqa: F401
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
    dishka,  # noqa: F401
    dishka_request,  # noqa: F401
    complex_scn,  # noqa: F401
    file_gateway,  # noqa: F401
    fixtures_resource_path,  # noqa: F401
    author,  # noqa: F401
    alembic_config,  # noqa: F401
    upgrade_schema_db,  # noqa: F401
    dcf,  # noqa: F401
    game_log,  # noqa: F401
)


@pytest_asyncio.fixture(scope="session")
async def api_config(dishka: AsyncContainer) -> ApiConfig:
    return await dishka.get(ApiConfig)


@pytest.fixture(scope="session")
def app(dishka: AsyncContainer):
    app = create_app()
    setup_dishka(dishka, app)
    return app


@pytest_asyncio.fixture(scope="session")
async def auth(dishka: AsyncContainer) -> AuthProperties:
    return AuthProperties(await dishka.get(AuthConfig))


@pytest.mark.anyio
@pytest_asyncio.fixture(scope="session")
async def client(app: FastAPI):
    async with (
        LifespanManager(app),
        AsyncClient(app=app, base_url="http://test") as ac,
    ):
        yield ac


@pytest_asyncio.fixture
async def user(dao: HolderDao, auth: AuthProperties) -> dto.User:
    user_ = await upsert_user(create_dto_harry(), dao.user)
    password = auth.get_password_hash("12345")
    await set_password(user_, password, dao.user)
    return user_
