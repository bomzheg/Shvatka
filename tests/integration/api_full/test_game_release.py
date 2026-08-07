import pytest
from dataclass_factory import Factory
from httpx import AsyncClient

from shvatka.api.app.dependencies.auth import AuthProperties
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
    actual = Factory().load(resp.json(), game_responses.GameRelease)
    assert actual.game_id == game.id
    assert actual.hints[0].type == HintType.text.name


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
