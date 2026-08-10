import pytest
from adaptix import Retort
from httpx import AsyncClient

from shvatka.api.app.dependencies.auth import AuthProperties
from shvatka.common.factory import REQUIRED_GAME_RECIPES
from shvatka.api.games import responses as game_responses
from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.models.enums import HintType
from shvatka.infrastructure.db.dao.holder import HolderDao

RELEASE_TEXT = "Игра пройдёт в тайной лаборатории"


def auth_cookies(auth: AuthProperties, player: dto.Player) -> dict[str, str]:
    return {"Authorization": "Bearer " + auth.create_user_token(player).access_token}


@pytest.mark.asyncio
async def test_no_release_by_default(
    game: dto.FullGame,
    client: AsyncClient,
):
    resp = await client.get(f"/games/{game.id}/release")
    assert resp.is_success
    resp.read()
    assert resp.json() is None


@pytest.mark.asyncio
async def test_save_release(
    game: dto.FullGame,
    check_dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
):
    resp = await client.put(
        f"/games/my/{game.id}/release",
        json={"hints": [{"type": "text", "text": RELEASE_TEXT}]},
        cookies=auth_cookies(auth, author),
    )
    assert resp.is_success

    saved = await check_dao.game.get_release(game.id)
    assert saved is not None
    hint = saved.hints[0]
    assert isinstance(hint, hints.TextHint)
    assert hint.text == RELEASE_TEXT

    # a release is promo — everyone sees it, guests included
    resp = await client.get(f"/games/{game.id}/release")
    assert resp.is_success
    resp.read()
    actual = Retort(recipe=[*REQUIRED_GAME_RECIPES]).load(resp.json(), game_responses.GameRelease)
    assert actual.game_id == game.id
    assert actual.hints[0].type == HintType.text.name


@pytest.mark.asyncio
async def test_save_release_with_a_banner(
    game: dto.FullGame,
    check_dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
):
    cookies = auth_cookies(auth, author)
    up = await client.post(
        f"/cdn/games/{game.id}/files",
        files={"file": ("banner.png", b"\x89PNG\r\n\x1a\n binary", "image/png")},
        cookies=cookies,
    )
    assert up.status_code == 200, up.text
    guid = up.json()["guid"]

    resp = await client.put(
        f"/games/my/{game.id}/release",
        json={
            "banner": {"type": "photo", "file_guid": guid, "caption": RELEASE_TEXT},
            "hints": [{"type": "text", "text": "карта района"}],
        },
        cookies=cookies,
    )
    assert resp.is_success, resp.text

    saved = await check_dao.game.get_release(game.id)
    assert saved is not None
    assert isinstance(saved.banner, hints.PhotoHint)
    assert saved.banner.file_guid == guid
    assert saved.banner.caption == RELEASE_TEXT
    # the banner leads the release, the rest follows
    assert len(saved.parts) == 2

    # guests get the banner too — the site shows it above the header
    resp = await client.get(f"/games/{game.id}/release")
    assert resp.is_success
    resp.read()
    actual = Retort(recipe=[*REQUIRED_GAME_RECIPES]).load(resp.json(), game_responses.GameRelease)
    assert actual.banner is not None
    assert actual.banner.file_guid == guid

    # and the file behind it is readable without auth
    resp = await client.get(f"/cdn/games/{game.id}/files/{guid}")
    assert resp.is_success


@pytest.mark.asyncio
async def test_banner_can_be_uploaded_after_the_game_started(
    game: dto.FullGame,
    dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
):
    """The scenario is frozen by then, but the release — and its banner — is not."""
    await dao.game.start(game)
    await dao.commit()

    cookies = auth_cookies(auth, author)
    up = await client.post(
        f"/cdn/games/{game.id}/files",
        files={"file": ("banner.png", b"\x89PNG\r\n\x1a\n binary", "image/png")},
        cookies=cookies,
    )
    assert up.status_code == 200, up.text

    resp = await client.put(
        f"/games/my/{game.id}/release",
        json={
            "banner": {"type": "photo", "file_guid": up.json()["guid"]},
            "hints": [],
        },
        cookies=cookies,
    )
    assert resp.is_success, resp.text


@pytest.mark.asyncio
async def test_admin_brings_a_banner_to_a_complete_game(
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
):
    """A complete game's release is the admin's to fix — banner included."""
    await dao.game.set_number(game, await dao.game.get_max_number() + 1)
    await dao.game.set_completed(game)
    await dao.commit()

    # harry's tg is in the configured superusers, and the game is not his
    cookies = auth_cookies(auth, harry)
    up = await client.post(
        f"/cdn/games/{game.id}/files",
        files={"file": ("banner.png", b"\x89PNG\r\n\x1a\n binary", "image/png")},
        cookies=cookies,
    )
    assert up.status_code == 200, up.text

    resp = await client.put(
        f"/games/my/{game.id}/release",
        json={
            "banner": {"type": "photo", "file_guid": up.json()["guid"]},
            "hints": [{"type": "text", "text": RELEASE_TEXT}],
        },
        cookies=cookies,
    )
    assert resp.is_success, resp.text
    saved = await check_dao.game.get_release(game.id)
    assert saved is not None
    assert saved.banner is not None


@pytest.mark.asyncio
async def test_admin_rewrites_a_release_keeping_the_authors_banner(
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
):
    """The banner stays the author's file — that must not block the admin."""
    up = await client.post(
        f"/cdn/games/{game.id}/files",
        files={"file": ("banner.png", b"\x89PNG\r\n\x1a\n binary", "image/png")},
        cookies=auth_cookies(auth, author),
    )
    assert up.status_code == 200, up.text
    banner = {"type": "photo", "file_guid": up.json()["guid"]}

    resp = await client.put(
        f"/games/my/{game.id}/release",
        json={"banner": banner, "hints": []},
        cookies=auth_cookies(auth, author),
    )
    assert resp.is_success, resp.text

    await dao.game.set_number(game, await dao.game.get_max_number() + 1)
    await dao.game.set_completed(game)
    await dao.commit()

    resp = await client.put(
        f"/games/my/{game.id}/release",
        json={"banner": banner, "hints": [{"type": "text", "text": RELEASE_TEXT}]},
        cookies=auth_cookies(auth, harry),
    )
    assert resp.is_success, resp.text
    saved = await check_dao.game.get_release(game.id)
    assert saved is not None
    assert len(saved.hints) == 1


@pytest.mark.asyncio
async def test_release_of_another_author_forbidden(
    game: dto.FullGame,
    check_dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    draco: dto.Player,
):
    # draco is an author, but not of this game — and not an admin either
    resp = await client.put(
        f"/games/my/{game.id}/release",
        json={"hints": [{"type": "text", "text": RELEASE_TEXT}]},
        cookies=auth_cookies(auth, draco),
    )
    assert not resp.is_success
    assert await check_dao.game.get_release(game.id) is None


@pytest.mark.asyncio
async def test_release_of_a_complete_game_is_admin_only(
    game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
):
    await dao.game.set_number(game, await dao.game.get_max_number() + 1)
    await dao.game.set_completed(game)
    await dao.commit()

    resp = await client.put(
        f"/games/my/{game.id}/release",
        json={"hints": [{"type": "text", "text": RELEASE_TEXT}]},
        cookies=auth_cookies(auth, author),
    )
    assert not resp.is_success
    assert await check_dao.game.get_release(game.id) is None

    # harry's tg is in the configured superusers
    resp = await client.put(
        f"/games/my/{game.id}/release",
        json={"hints": [{"type": "text", "text": RELEASE_TEXT}]},
        cookies=auth_cookies(auth, harry),
    )
    assert resp.is_success
    assert await check_dao.game.get_release(game.id) is not None


@pytest.mark.asyncio
async def test_delete_release(
    game: dto.FullGame,
    check_dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
):
    cookies = auth_cookies(auth, author)
    resp = await client.put(
        f"/games/my/{game.id}/release",
        json={"hints": [{"type": "text", "text": RELEASE_TEXT}]},
        cookies=cookies,
    )
    assert resp.is_success

    resp = await client.request("DELETE", f"/games/my/{game.id}/release", cookies=cookies)
    assert resp.is_success
    assert await check_dao.game.get_release(game.id) is None
