import pytest
from httpx import AsyncClient

from shvatka.api.dependencies.auth import AuthProperties
from shvatka.core.models import dto
from shvatka.core.models.enums import OrgPermission
from shvatka.infrastructure.db.dao.holder import HolderDao


def auth_cookies(auth: AuthProperties, player: dto.Player) -> dict[str, str]:
    token = auth.create_user_token(player)
    return {"Authorization": "Bearer " + token.access_token}


@pytest.mark.asyncio
async def test_list_orgs_only_primary(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    game: dto.FullGame,
):
    resp = await client.get(
        f"/games/{game.id}/organizers",
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 200, resp.text
    content = resp.json()["content"]
    assert len(content) == 1
    primary = content[0]
    # primary org is the author and is reported with a null org_id
    assert primary["org_id"] is None
    assert primary["player"]["id"] == author.id
    assert primary["can_spy"] is True
    assert primary["deleted"] is False


@pytest.mark.asyncio
async def test_list_orgs_forbidden_for_stranger(
    client: AsyncClient,
    auth: AuthProperties,
    harry: dto.Player,
    game: dto.FullGame,
):
    # game is not completed and harry is neither author nor organizer
    resp = await client.get(
        f"/games/{game.id}/organizers",
        cookies=auth_cookies(auth, harry),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "IsNotOrganizer"


@pytest.mark.asyncio
async def test_list_orgs_public_when_completed(
    client: AsyncClient,
    auth: AuthProperties,
    harry: dto.Player,
    game: dto.FullGame,
    dao: HolderDao,
):
    await dao.game.set_completed(game)
    await dao.commit()
    # for a completed game even a stranger may view the organizers
    resp = await client.get(
        f"/games/{game.id}/organizers",
        cookies=auth_cookies(auth, harry),
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["content"]) == 1


@pytest.mark.asyncio
async def test_add_org(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    game: dto.FullGame,
    check_dao: HolderDao,
):
    resp = await client.post(
        f"/games/{game.id}/organizers",
        json={"player_id": harry.id},
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["org_id"] is not None
    assert body["player"]["id"] == harry.id
    assert body["deleted"] is False
    assert body["can_spy"] is False

    secondary = await check_dao.organizer.get_orgs(game)
    assert len(secondary) == 1
    assert secondary[0].player.id == harry.id

    # the new org now appears in the listing alongside the primary org
    resp = await client.get(
        f"/games/{game.id}/organizers",
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 200, resp.text
    ids = {org["player"]["id"] for org in resp.json()["content"]}
    assert ids == {author.id, harry.id}


@pytest.mark.asyncio
async def test_add_org_forbidden_for_non_author(
    client: AsyncClient,
    auth: AuthProperties,
    harry: dto.Player,
    game: dto.FullGame,
):
    resp = await client.post(
        f"/games/{game.id}/organizers",
        json={"player_id": harry.id},
        cookies=auth_cookies(auth, harry),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "GameHasAnotherAuthor"


@pytest.mark.asyncio
async def test_add_org_twice_rejected(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    game: dto.FullGame,
):
    cookies = auth_cookies(auth, author)
    first = await client.post(
        f"/games/{game.id}/organizers", json={"player_id": harry.id}, cookies=cookies
    )
    assert first.status_code == 200, first.text
    second = await client.post(
        f"/games/{game.id}/organizers", json={"player_id": harry.id}, cookies=cookies
    )
    assert second.status_code == 422, second.text
    assert second.json()["type"] == "PlayerAlreadyOrganizer"


@pytest.mark.asyncio
async def test_restore_org_via_post(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    org = await dao.organizer.add_new(game, harry)
    await dao.organizer.flip_deleted(org)
    await dao.commit()
    assert (await check_dao.organizer.get_by_id(org.id)).deleted is True

    cookies = auth_cookies(auth, author)
    resp = await client.post(
        f"/games/{game.id}/organizers",
        json={"player_id": harry.id},
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # the same org is restored, not a duplicate created
    assert body["org_id"] == org.id
    assert body["deleted"] is False
    assert (await check_dao.organizer.get_by_id(org.id)).deleted is False
    assert len(await check_dao.organizer.get_orgs(game, with_deleted=True)) == 1


@pytest.mark.asyncio
async def test_change_org_permission(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    org = await dao.organizer.add_new(game, harry)
    await dao.commit()
    cookies = auth_cookies(auth, author)

    resp = await client.put(
        f"/games/{game.id}/organizers/{org.id}",
        json={"permission": OrgPermission.can_spy.name, "value": True},
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["can_spy"] is True
    stored = await check_dao.organizer.get_by_id(org.id)
    assert stored.can_spy is True

    # idempotent: setting the same value again keeps it enabled
    resp = await client.put(
        f"/games/{game.id}/organizers/{org.id}",
        json={"permission": OrgPermission.can_spy.name, "value": True},
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["can_spy"] is True

    # and it can be turned back off
    resp = await client.put(
        f"/games/{game.id}/organizers/{org.id}",
        json={"permission": OrgPermission.can_spy.name, "value": False},
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["can_spy"] is False


@pytest.mark.asyncio
async def test_change_org_permission_unknown(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    game: dto.FullGame,
    dao: HolderDao,
):
    org = await dao.organizer.add_new(game, harry)
    await dao.commit()
    resp = await client.put(
        f"/games/{game.id}/organizers/{org.id}",
        json={"permission": "not_a_permission", "value": True},
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_delete_org(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    org = await dao.organizer.add_new(game, harry)
    await dao.commit()
    cookies = auth_cookies(auth, author)

    resp = await client.request(
        "DELETE",
        f"/games/{game.id}/organizers",
        json={"org_id": org.id},
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["deleted"] is True
    stored = await check_dao.organizer.get_by_id(org.id)
    assert stored.deleted is True

    # not listed among the active orgs anymore ...
    assert await check_dao.organizer.get_orgs(game) == []
    # ... but still present (with deleted=True) in the api listing
    listing = await client.get(f"/games/{game.id}/organizers", cookies=cookies)
    assert listing.status_code == 200, listing.text
    harry_org = next(o for o in listing.json()["content"] if o["player"]["id"] == harry.id)
    assert harry_org["deleted"] is True

    # deleting again is idempotent
    resp = await client.request(
        "DELETE",
        f"/games/{game.id}/organizers",
        json={"org_id": org.id},
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["deleted"] is True
