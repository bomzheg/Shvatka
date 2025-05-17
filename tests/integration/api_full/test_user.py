import pytest
import pytest_asyncio
from httpx import AsyncClient

from shvatka.api.dependencies.auth import AuthProperties
from shvatka.api.models.auth import Token
from shvatka.core.models import dto
from shvatka.core.services.user import upsert_user, set_password
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.identity import MockIdentityProvider
from tests.fixtures.user_constants import create_dto_harry


@pytest_asyncio.fixture
async def user(dao: HolderDao, auth: AuthProperties) -> dto.User:
    user_ = await upsert_user(create_dto_harry(), dao.user)
    password = auth.get_password_hash("12345")
    await set_password(MockIdentityProvider(user=user_), password, dao.user)
    return user_


@pytest.fixture
def token(user: dto.User, auth: AuthProperties) -> Token:
    return auth.create_user_token(user)


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, user: dto.User):
    resp_user = await client.get(f"/users/{user.db_id}")
    assert resp_user.is_success
    resp_user.read()
    actual_user = dto.User(**resp_user.json())
    assert user == actual_user


@pytest.mark.asyncio
async def test_auth(client: AsyncClient, user: dto.User, auth: AuthProperties, dao: HolderDao):
    resp = await client.post(
        "/auth/token",
        data={"username": user.username, "password": "12345"},
    )
    assert resp.is_success
    resp.read()
    access_token = resp.cookies.get("Authorization").removeprefix('"').removesuffix('"')
    actual_user = await auth.get_current_user(
        Token(access_token=access_token.removeprefix("bearer "), token_type="bearer"),
        dao,
    )
    assert user == actual_user


@pytest.mark.asyncio
async def test_user_get(client: AsyncClient, user: dto.User, token: Token):
    resp = await client.get(
        "/users/me",
        cookies={"Authorization": f"{token.token_type} {token.access_token}"},
        follow_redirects=True,
    )

    assert resp.is_success
    actual = dto.User(**resp.json())
    assert user == actual


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, token: Token):
    resp = await client.post(
        "/auth/logout",
        cookies={"Authorization": f"{token.token_type} {token.access_token}"},
        follow_redirects=True,
    )

    assert resp.is_success
    assert not resp.cookies
    assert 'Authorization=""' in resp.headers["set-cookie"]


@pytest.mark.asyncio
@pytest.mark.skip(reason="doesnt work. TODO")
async def test_change_password(client: AsyncClient, user: dto.User, token: Token):
    resp = await client.put(
        "/users/me/password/",
        cookies={"Authorization": f"{token.token_type} {token.access_token}"},
        json="09876",
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
