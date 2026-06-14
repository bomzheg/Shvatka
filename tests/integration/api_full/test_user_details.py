import pytest
from httpx import AsyncClient

from shvatka.core.models import dto
from shvatka.core.utils.defaults_constants import CAPTAIN_ROLE
from shvatka.infrastructure.db.dao.holder import HolderDao


@pytest.mark.asyncio
async def test_get_user_details(
    client: AsyncClient,
    harry: dto.Player,
    gryffindor: dto.Team,
):
    resp = await client.get(f"/users/{harry.id}/details")
    assert resp.is_success
    resp.read()
    body = resp.json()
    assert body["id"] == harry.id
    assert body["username"] == harry.username
    assert body["can_be_author"] == harry.can_be_author
    assert body["tg"]["tg_id"] == harry.get_chat_id()
    assert body["tg"]["username"] == harry.get_tg_username()
    assert body["player_in_team"] is not None
    assert body["player_in_team"]["id"] is not None
    assert body["player_in_team"]["team"]["id"] == gryffindor.id
    assert body["player_in_team"]["role"] == CAPTAIN_ROLE


@pytest.mark.asyncio
async def test_get_user_details_without_team(
    client: AsyncClient,
    hermione: dto.Player,
):
    resp = await client.get(f"/users/{hermione.id}/details")
    assert resp.is_success
    resp.read()
    body = resp.json()
    assert body["id"] == hermione.id
    assert body["player_in_team"] is None


@pytest.mark.asyncio
async def test_search_users_by_username(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
):
    resp = await client.get("/users", params={"username": harry.username}, follow_redirects=True)
    assert resp.is_success
    resp.read()
    items = resp.json()["items"]
    ids = [item["id"] for item in items]
    assert harry.id in ids
    assert hermione.id not in ids


@pytest.mark.asyncio
async def test_search_users_by_name(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
):
    resp = await client.get("/users", params={"name": "Hermione"}, follow_redirects=True)
    assert resp.is_success
    resp.read()
    items = resp.json()["items"]
    ids = [item["id"] for item in items]
    assert hermione.id in ids
    assert harry.id not in ids


@pytest.mark.asyncio
async def test_search_users_archive_excludes_tg(
    client: AsyncClient,
    harry: dto.Player,
    dao: HolderDao,
):
    # archive only -> only forum users (without tg). harry has tg, so excluded.
    resp = await client.get(
        "/users",
        params={"username": harry.username, "active": False, "archive": True},
        follow_redirects=True,
    )
    assert resp.is_success
    resp.read()
    ids = [item["id"] for item in resp.json()["items"]]
    assert harry.id not in ids
