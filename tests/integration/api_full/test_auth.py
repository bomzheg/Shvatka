import pytest
from httpx import AsyncClient

from shvatka.core.models import dto
from shvatka.infrastructure.db.dao.holder import HolderDao


@pytest.fixture
async def harry_with_verified_email(harry: dto.Player, dao: HolderDao) -> dto.Player:
    await dao.email.add_email_to_player(harry, "harry@example.com")
    await dao.email.set_verified("harry@example.com")
    await dao.commit()
    return harry


@pytest.mark.asyncio
async def test_forgot_password_ok_for_verified_email(
    client: AsyncClient, harry_with_verified_email: dto.Player
):
    resp = await client.post("/auth/forgot-password", json={"email": "harry@example.com"})
    assert resp.is_success
    assert resp.json() == {"ok": True}


@pytest.mark.asyncio
async def test_forgot_password_does_not_disclose_unknown_email(client: AsyncClient):
    resp = await client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert resp.is_success
    assert resp.json() == {"ok": True}


@pytest.mark.asyncio
async def test_forgot_password_is_rate_limited(client: AsyncClient):
    first = await client.post("/auth/forgot-password", json={"email": "rate-limited@example.com"})
    assert first.is_success

    second = await client.post("/auth/forgot-password", json={"email": "rate-limited@example.com"})
    assert second.status_code == 429
