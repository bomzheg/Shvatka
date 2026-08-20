import os
from datetime import datetime, timedelta
from pathlib import PurePath

import pytest
from httpx import AsyncClient

from shvatka.api.app.dependencies.auth import AuthProperties
from shvatka.api.auth.responses import Token
from shvatka.core.files.interactors import STORAGE_ORPHAN_MIN_AGE
from shvatka.core.models import dto
from shvatka.core.services.game import create_game
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.clients.file_storage import LocalFileStorage
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.scn_fixtures import GUID


def auth_cookies(token: Token) -> dict[str, str]:
    return {"Authorization": f"{token.token_type} {token.access_token}"}


def author_cookies(auth: AuthProperties, player: dto.Player) -> dict[str, str]:
    return {"Authorization": "Bearer " + auth.create_user_token(player).access_token}


async def upload(client: AsyncClient, game_id: int, cookies: dict[str, str]) -> str:
    resp = await client.post(
        f"/cdn/games/{game_id}/files",
        files={"file": ("note.txt", b"hello world", "text/plain")},
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["guid"]


def age(path: str) -> None:
    """Backdate the content so the garbage collector stops sparing it."""
    when = (datetime.now(tz=tz_utc) - STORAGE_ORPHAN_MIN_AGE - timedelta(hours=1)).timestamp()
    os.utime(path, (when, when))


@pytest.mark.asyncio
async def test_gc_dry_run_changes_nothing(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
):
    game = await create_game(author=author, name="draft for gc dry run", dao=dao.game_creator)
    guid = await upload(client, game.id, author_cookies(auth, author))
    (file_id,) = await check_dao.file_info.get_ids_by_guids([guid])

    resp = await client.post(
        "/admin/files/gc", cookies=auth_cookies(auth.create_user_token(harry))
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["dry_run"] is True
    assert {"game_id": game.id, "file_id": file_id} in body["game_links"]
    assert guid in body["file_guids"]
    # ... and nothing was actually removed
    assert await check_dao.game_file.get_file_ids(game.id) == {file_id}
    assert await check_dao.file_info.get_ids_by_guids([guid]) == [file_id]


@pytest.mark.asyncio
async def test_gc_deletes_unused_link_and_meta(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
    local_storage: LocalFileStorage,
):
    game = await create_game(author=author, name="draft for gc", dao=dao.game_creator)
    guid = await upload(client, game.id, author_cookies(auth, author))
    (file_id,) = await check_dao.file_info.get_ids_by_guids([guid])
    meta = await check_dao.file_info.get_by_guid(guid)
    path = meta.file_content_link.file_path

    cookies = auth_cookies(auth.create_user_token(harry))
    resp = await client.post("/admin/files/gc?dry_run=false", cookies=cookies)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["dry_run"] is False
    assert {"game_id": game.id, "file_id": file_id} in body["game_links"]
    assert guid in body["file_guids"]
    assert await check_dao.game_file.get_file_ids(game.id) == set()
    assert await check_dao.file_info.get_ids_by_guids([guid]) == []
    # the content is younger than the grace period, so it is spared for now
    assert await local_storage.exists(meta.file_content_link)
    assert PurePath(path).name not in body["stored_files"]

    age(path)
    resp = await client.post("/admin/files/gc?dry_run=false", cookies=cookies)
    assert resp.status_code == 200, resp.text
    assert not await local_storage.exists(meta.file_content_link)


@pytest.mark.asyncio
async def test_gc_keeps_files_a_level_uses(
    client: AsyncClient,
    auth: AuthProperties,
    harry: dto.Player,
    game: dto.FullGame,
    check_dao: HolderDao,
    local_storage: LocalFileStorage,
):
    (file_id,) = await check_dao.file_info.get_ids_by_guids([GUID])
    meta = await check_dao.file_info.get_by_guid(GUID)
    age(meta.file_content_link.file_path)

    resp = await client.post(
        "/admin/files/gc?dry_run=false",
        cookies=auth_cookies(auth.create_user_token(harry)),
    )
    assert resp.status_code == 200, resp.text
    assert await check_dao.game_file.get_file_ids(game.id) == {file_id}
    assert await check_dao.file_info.get_ids_by_guids([GUID]) == [file_id]
    assert await local_storage.exists(meta.file_content_link)


@pytest.mark.asyncio
async def test_gc_keeps_files_the_release_uses(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
    local_storage: LocalFileStorage,
):
    """A banner has no ``level_files`` row — only the release itself knows it."""
    game = await create_game(author=author, name="draft with a banner", dao=dao.game_creator)
    author_auth = author_cookies(auth, author)
    guid = await upload(client, game.id, author_auth)
    (file_id,) = await check_dao.file_info.get_ids_by_guids([guid])
    saved = await client.put(
        f"/games/my/{game.id}/release",
        json={"banner": {"type": "photo", "file_guid": guid, "caption": "тема"}, "hints": []},
        cookies=author_auth,
    )
    assert saved.is_success, saved.text
    meta = await check_dao.file_info.get_by_guid(guid)
    age(meta.file_content_link.file_path)

    resp = await client.post(
        "/admin/files/gc?dry_run=false",
        cookies=auth_cookies(auth.create_user_token(harry)),
    )
    assert resp.status_code == 200, resp.text
    assert await check_dao.game_file.get_file_ids(game.id) == {file_id}
    assert await check_dao.file_info.get_ids_by_guids([guid]) == [file_id]
    assert await local_storage.exists(meta.file_content_link)


@pytest.mark.asyncio
async def test_gc_forbidden_for_non_superuser(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
):
    resp = await client.post("/admin/files/gc", cookies=author_cookies(auth, author))
    assert resp.status_code == 403, resp.text
