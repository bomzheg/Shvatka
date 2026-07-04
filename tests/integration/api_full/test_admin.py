import pytest
import pytest_asyncio
from httpx import AsyncClient

from shvatka.api.dependencies.auth import AuthProperties
from shvatka.api.models.auth import Token
from shvatka.core.models import dto
from shvatka.core.players.player import upsert_player
from shvatka.core.services.user import upsert_user
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.user_constants import create_dto_hermione


def auth_cookies(token: Token) -> dict[str, str]:
    return {"Authorization": f"{token.token_type} {token.access_token}"}


@pytest_asyncio.fixture
async def hermione(dao: HolderDao) -> dto.Player:
    # tg_id 13 — deliberately not in the configured superusers list
    user_ = await upsert_user(create_dto_hermione(), dao.user)
    return await upsert_player(user_, dao.player)


@pytest.fixture
def admin_token(harry: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(harry)


@pytest.fixture
def hermione_token(hermione: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(hermione)


@pytest.mark.asyncio
async def test_admin_endpoint_forbidden_for_non_superuser(
    client: AsyncClient, hermione_token: Token
):
    resp = await client.get(
        "/admin/players",
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_users_me_is_admin_flag(
    client: AsyncClient, admin_token: Token, hermione_token: Token
):
    admin_resp = await client.get(
        "/users/me", cookies=auth_cookies(admin_token), follow_redirects=True
    )
    assert admin_resp.json()["is_admin"] is True
    plain_resp = await client.get(
        "/users/me", cookies=auth_cookies(hermione_token), follow_redirects=True
    )
    assert plain_resp.json()["is_admin"] is False


@pytest.mark.asyncio
async def test_list_players(
    client: AsyncClient, admin_token: Token, harry: dto.Player, hermione: dto.Player
):
    resp = await client.get(
        "/admin/players",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    ids = {item["id"] for item in resp.json()["items"]}
    assert harry.id in ids
    assert hermione.id in ids


@pytest.mark.asyncio
async def test_list_players_filter_can_be_author(
    client: AsyncClient, admin_token: Token, harry: dto.Player, hermione: dto.Player
):
    resp = await client.get(
        "/admin/players",
        params={"can_be_author": True},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    ids = {item["id"] for item in resp.json()["items"]}
    assert harry.id in ids  # harry is promoted
    assert hermione.id not in ids  # hermione is not


@pytest.mark.asyncio
async def test_create_one_time_link(client: AsyncClient, admin_token: Token, hermione: dto.Player):
    resp = await client.post(
        f"/admin/players/{hermione.id}/one-time-link",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    assert "/auth/one-time-token?token=" in resp.json()["url"]


@pytest.mark.asyncio
async def test_change_email_verified(
    client: AsyncClient,
    admin_token: Token,
    hermione: dto.Player,
    check_dao: HolderDao,
):
    resp = await client.put(
        f"/admin/players/{hermione.id}/email",
        json={"email": "hermione@example.org", "verified": True},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    body = resp.json()
    assert body["email"] == "hermione@example.org"
    assert body["is_verified"] is True
    stored = await check_dao.email.get_by_player_id(hermione.id)
    assert stored is not None
    assert stored.email == "hermione@example.org"
    assert stored.is_verified is True


@pytest.mark.asyncio
async def test_change_email_unverified(
    client: AsyncClient,
    admin_token: Token,
    hermione: dto.Player,
    check_dao: HolderDao,
):
    resp = await client.put(
        f"/admin/players/{hermione.id}/email",
        json={"email": "hermione2@example.org", "verified": False},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    assert resp.json()["is_verified"] is False
    stored = await check_dao.email.get_by_player_id(hermione.id)
    assert stored is not None
    assert stored.is_verified is False


@pytest.mark.asyncio
async def test_change_tg(
    client: AsyncClient,
    admin_token: Token,
    hermione: dto.Player,
    check_dao: HolderDao,
):
    new_tg_id = 555_000_111
    resp = await client.put(
        f"/admin/players/{hermione.id}/tg",
        json={"tg_id": new_tg_id, "username": "new_hermione", "first_name": "Herm"},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    assert resp.json()["tg"]["tg_id"] == new_tg_id
    reloaded = await check_dao.player.get_by_id(hermione.id)
    assert reloaded.get_chat_id() == new_tg_id


@pytest.mark.asyncio
async def test_change_tg_conflict(
    client: AsyncClient,
    admin_token: Token,
    harry: dto.Player,
    hermione: dto.Player,
):
    # harry's tg is already linked to harry; linking it to hermione must conflict
    resp = await client.put(
        f"/admin/players/{hermione.id}/tg",
        json={"tg_id": harry.get_chat_id()},
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_poll_empty(client: AsyncClient, admin_token: Token):
    resp = await client.get(
        "/admin/poll",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.is_success
    assert resp.json() == {"teams": []}


@pytest.mark.asyncio
async def test_remove_poll_vote(client: AsyncClient, admin_token: Token, hermione: dto.Player):
    resp = await client.delete(
        f"/admin/poll/1/players/{hermione.id}",
        cookies=auth_cookies(admin_token),
        follow_redirects=True,
    )
    assert resp.status_code == 204
