import pytest
from httpx import AsyncClient

from shvatka.api.dependencies import AuthProvider
from shvatka.core.models import dto


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
