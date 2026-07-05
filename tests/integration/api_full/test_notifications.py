import pytest
from httpx import AsyncClient

from shvatka.api.dependencies.auth import AuthProperties
from shvatka.api.models.auth import Token
from shvatka.core.models import dto
from shvatka.infrastructure.db.dao.holder import HolderDao


def auth_cookies(token: Token) -> dict[str, str]:
    return {"Authorization": f"{token.token_type} {token.access_token}"}


@pytest.fixture
def harry_token(harry: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(harry)


@pytest.fixture
def hermione_token(hermione: dto.Player, auth: AuthProperties) -> Token:
    return auth.create_user_token(hermione)


@pytest.mark.asyncio
async def test_feed_after_join(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    harry_token: Token,
    hermione_token: Token,
):
    add = await client.post(
        f"/teams/{gryffindor.id}/players",
        cookies=auth_cookies(harry_token),
        json={"player_id": hermione.id},
        follow_redirects=True,
    )
    assert add.is_success

    resp = await client.get(
        "/notifications", cookies=auth_cookies(hermione_token), follow_redirects=True
    )
    assert resp.is_success
    resp.read()
    items = resp.json()["items"]
    assert any(n["type"] == "player_joined_team" for n in items)
    joined = next(n for n in items if n["type"] == "player_joined_team")
    assert joined["payload"]["player_id"] == hermione.id
    assert joined["read"] is False


@pytest.mark.asyncio
async def test_unread_count_and_mark_read(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    harry_token: Token,
    hermione_token: Token,
):
    await client.post(
        f"/teams/{gryffindor.id}/players",
        cookies=auth_cookies(harry_token),
        json={"player_id": hermione.id},
        follow_redirects=True,
    )
    count = await client.get(
        "/notifications/unread-count",
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    count.read()
    assert count.json()["count"] >= 1

    read_all = await client.put(
        "/notifications/read-all",
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert read_all.status_code == 204

    count2 = await client.get(
        "/notifications/unread-count",
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    count2.read()
    assert count2.json()["count"] == 0


@pytest.mark.asyncio
async def test_team_join_invite_and_accept(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    harry_token: Token,
    hermione_token: Token,
    check_dao: HolderDao,
):
    invite = await client.post(
        "/requests/team-join-invite",
        cookies=auth_cookies(harry_token),
        json={"team_id": gryffindor.id, "player_id": hermione.id, "role": "seeker"},
        follow_redirects=True,
    )
    assert invite.is_success
    invite.read()
    request_id = invite.json()["id"]
    assert invite.json()["status"] == "pending"

    # hermione sees the invite as incoming
    incoming = await client.get(
        "/requests",
        params={"direction": "incoming", "pending": True},
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    incoming.read()
    assert request_id in [r["id"] for r in incoming.json()["items"]]

    # hermione accepts -> joins the team
    accept = await client.post(
        f"/requests/{request_id}/accept",
        cookies=auth_cookies(hermione_token),
        follow_redirects=True,
    )
    assert accept.is_success
    accept.read()
    assert accept.json()["status"] == "accepted"

    assert await check_dao.team_player.get_team(hermione) is not None


@pytest.mark.asyncio
async def test_team_join_invite_accept_forbidden_for_stranger(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    ron: dto.Player,
    gryffindor: dto.Team,
    harry_token: Token,
    auth: AuthProperties,
):
    invite = await client.post(
        "/requests/team-join-invite",
        cookies=auth_cookies(harry_token),
        json={"team_id": gryffindor.id, "player_id": hermione.id},
        follow_redirects=True,
    )
    invite.read()
    request_id = invite.json()["id"]

    ron_token = auth.create_user_token(ron)
    resp = await client.post(
        f"/requests/{request_id}/accept",
        cookies=auth_cookies(ron_token),
        follow_redirects=True,
    )
    assert resp.status_code == 422  # RequestPermissionError -> SHError


@pytest.mark.asyncio
async def test_join_request_and_accept_by_captain(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    harry_token: Token,
    hermione_token: Token,
    check_dao: HolderDao,
):
    ask = await client.post(
        "/requests/team-join",
        cookies=auth_cookies(hermione_token),
        json={"team_id": gryffindor.id},
        follow_redirects=True,
    )
    assert ask.is_success
    ask.read()
    request_id = ask.json()["id"]

    accept = await client.post(
        f"/requests/{request_id}/accept",
        cookies=auth_cookies(harry_token),
        follow_redirects=True,
    )
    assert accept.is_success
    accept.read()
    assert accept.json()["status"] == "accepted"
    assert await check_dao.team_player.get_team(hermione) is not None


@pytest.mark.asyncio
async def test_cancel_own_invite(
    client: AsyncClient,
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    harry_token: Token,
):
    invite = await client.post(
        "/requests/team-join-invite",
        cookies=auth_cookies(harry_token),
        json={"team_id": gryffindor.id, "player_id": hermione.id},
        follow_redirects=True,
    )
    invite.read()
    request_id = invite.json()["id"]

    cancel = await client.post(
        f"/requests/{request_id}/cancel",
        cookies=auth_cookies(harry_token),
        follow_redirects=True,
    )
    assert cancel.is_success
    cancel.read()
    assert cancel.json()["status"] == "cancelled"
