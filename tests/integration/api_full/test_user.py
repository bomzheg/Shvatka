import pytest
from httpx import AsyncClient

from shvatka.api.dependencies.auth import AuthProperties
from shvatka.api.models import responses
from shvatka.api.models.auth import Token
from shvatka.core.models import dto
from shvatka.infrastructure.db.dao.holder import HolderDao


@pytest.fixture
def token(harry: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(harry)


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, harry: dto.Player):
    resp_user = await client.get(f"/users/{harry.id}")
    assert resp_user.is_success
    resp_user.read()
    actual = responses.Player(**resp_user.json())
    assert responses.Player.from_core(harry) == actual
    assert actual.id == harry.id
    assert actual.name_mention == harry.username
    assert actual.can_be_author == harry.can_be_author


@pytest.mark.asyncio
async def test_auth(client: AsyncClient, harry: dto.Player, auth: AuthProperties, dao: HolderDao):
    resp = await client.post(
        "/auth/token",
        data={"username": harry.username, "password": "12345"},
    )
    assert resp.is_success
    resp.read()
    access_token = resp.cookies.get("Authorization").removeprefix('"').removesuffix('"')
    actual_user = await auth.get_current_user(
        Token(access_token=access_token.removeprefix("bearer "), token_type="bearer"),
        dao,
    )
    assert harry == actual_user


@pytest.mark.asyncio
async def test_user_get(client: AsyncClient, harry: dto.Player, token: Token):
    resp = await client.get(
        "/users/me",
        cookies={"Authorization": f"{token.token_type} {token.access_token}"},
        follow_redirects=True,
    )

    assert resp.is_success
    actual = responses.Player(**resp.json())
    assert responses.Player.from_core(harry) == actual
    assert actual.id == harry.id
    assert actual.name_mention == harry.username
    assert actual.can_be_author == harry.can_be_author


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
async def test_change_password(client: AsyncClient, harry: dto.Player, token: Token):
    resp = await client.put(
        "/users/me/password/",
        cookies={"Authorization": f"{token.token_type} {token.access_token}"},
        json="09876",
        follow_redirects=True,
    )
    assert resp.is_success

    resp = await client.post(
        "/auth/token",
        data={"username": harry.username, "password": "12345"},
    )
    assert not resp.is_success

    resp = await client.post(
        "/auth/token",
        data={"username": harry.username, "password": "09876"},
    )
    assert resp.is_success
