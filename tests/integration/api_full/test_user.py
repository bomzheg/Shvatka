import pytest
import pytest_asyncio
from httpx import AsyncClient

from src.api.dependencies import AuthProvider
from src.infrastructure.db.dao.holder import HolderDao
from src.shvatka.models import dto
from src.shvatka.services.user import set_password, upsert_user
from tests.fixtures.user_constants import create_dto_harry


@pytest_asyncio.fixture
async def user(dao: HolderDao, auth: AuthProvider) -> dto.User:
    user_ = await upsert_user(create_dto_harry(), dao.user)
    password = auth.get_password_hash("12345")
    await set_password(user_, password, dao.user)
    return user_


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, user: dto.User):
    resp_user = await client.get(f"/users/{user.db_id}")
    assert resp_user.is_success
    resp_user.read()
    actual_user = dto.User(**resp_user.json())
    assert user == actual_user


@pytest.mark.asyncio
async def test_auth(client: AsyncClient, user: dto.User):
    resp = await client.post(
        "/auth/token",
        data={"username": user.username, "password": "12345"},
    )
    assert resp.is_success
    resp.read()
    access_token = resp.json()["access_token"]

    resp = await client.get(
        "/users/me/",
        headers={"Authorization": "Bearer " + access_token},
        follow_redirects=True,
    )
    assert resp.is_success
    resp.read()
    actual_user = dto.User(**resp.json())
    assert user == actual_user


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, user: dto.User, auth: AuthProvider):
    token = auth.create_user_token(user)
    resp = await client.put(
        "/users/me/password/",
        headers={"Authorization": "Bearer " + token.access_token},
        json={"password": "09876"},
        follow_redirects=True,
    )
    assert resp.is_success

    resp = await client.post(
        "/auth/token",
        data={"username": user.username, "password": "12345"},
    )
    assert not resp.is_success

    resp = await client.post(
        "/auth/token",
        data={"username": user.username, "password": "09876"},
    )
    assert resp.is_success
