import pytest
from httpx import AsyncClient
from sqlalchemy.exc import NoResultFound

from shvatka.api.app.dependencies.auth import AuthProperties
from shvatka.core.models import dto
from shvatka.core.services.game import create_game
from shvatka.infrastructure.clients.file_storage import LocalFileStorage
from shvatka.infrastructure.db.dao.complex.game import GameCreatorImpl
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.scn_fixtures import GUID


def auth_cookies(auth: AuthProperties, player: dto.Player) -> dict[str, str]:
    return {"Authorization": "Bearer " + auth.create_user_token(player).access_token}


async def upload(client: AsyncClient, game_id: int, cookies: dict[str, str]) -> str:
    resp = await client.post(
        f"/cdn/games/{game_id}/files",
        files={"file": ("note.txt", b"hello world", "text/plain")},
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["guid"]


@pytest.mark.asyncio
async def test_delete_unused_game_file(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
    local_storage: LocalFileStorage,
):
    game = await create_game(author=author, name="draft delete file", dao=GameCreatorImpl(dao))
    cookies = auth_cookies(auth, author)
    guid = await upload(client, game.id, cookies)
    (file_id,) = await check_dao.file_info.get_ids_by_guids([guid])
    meta = await check_dao.file_info.get_by_guid(guid)

    resp = await client.delete(f"/cdn/games/{game.id}/files/{guid}", cookies=cookies)
    assert resp.status_code == 204, resp.text

    # nothing links to it any more, so the file itself is gone with its link
    assert await check_dao.game_file.get_file_ids(game.id) == set()
    assert file_id not in await check_dao.file_info.get_ids_by_guids([guid])
    with pytest.raises(NoResultFound):
        await check_dao.file_info.get_by_guid(guid)
    assert not await local_storage.exists(meta.file_content_link)


@pytest.mark.asyncio
async def test_cant_delete_file_used_by_a_level(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    game: dto.FullGame,
    check_dao: HolderDao,
):
    resp = await client.delete(
        f"/cdn/games/{game.id}/files/{GUID}",
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 409, resp.text
    (file_id,) = await check_dao.file_info.get_ids_by_guids([GUID])
    assert file_id in await check_dao.game_file.get_file_ids(game.id)


@pytest.mark.asyncio
async def test_cant_delete_file_used_by_the_release(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
):
    game = await create_game(author=author, name="draft release file", dao=GameCreatorImpl(dao))
    cookies = auth_cookies(auth, author)
    guid = await upload(client, game.id, cookies)
    saved = await client.put(
        f"/games/my/{game.id}/release",
        json={"banner": {"type": "photo", "file_guid": guid, "caption": "тема"}, "hints": []},
        cookies=cookies,
    )
    assert saved.is_success, saved.text

    resp = await client.delete(f"/cdn/games/{game.id}/files/{guid}", cookies=cookies)
    assert resp.status_code == 409, resp.text
    (file_id,) = await check_dao.file_info.get_ids_by_guids([guid])
    assert file_id in await check_dao.game_file.get_file_ids(game.id)


@pytest.mark.asyncio
async def test_delete_keeps_a_file_another_game_still_uses(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
    local_storage: LocalFileStorage,
):
    game = await create_game(author=author, name="draft shared file", dao=GameCreatorImpl(dao))
    other = await create_game(author=author, name="draft shared file 2", dao=GameCreatorImpl(dao))
    cookies = auth_cookies(auth, author)
    guid = await upload(client, game.id, cookies)
    (file_id,) = await check_dao.file_info.get_ids_by_guids([guid])
    await dao.game_file.add_game_files(other.id, [file_id])
    await dao.commit()
    meta = await check_dao.file_info.get_by_guid(guid)

    resp = await client.delete(f"/cdn/games/{game.id}/files/{guid}", cookies=cookies)
    assert resp.status_code == 204, resp.text

    # only this game's link goes; the file is still the other game's to use
    assert await check_dao.game_file.get_file_ids(game.id) == set()
    assert await check_dao.game_file.get_file_ids(other.id) == {file_id}
    assert (await check_dao.file_info.get_by_guid(guid)).guid == guid
    assert await local_storage.exists(meta.file_content_link)


@pytest.mark.asyncio
async def test_delete_file_not_in_game(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
):
    game = await create_game(author=author, name="draft delete missing", dao=GameCreatorImpl(dao))
    resp = await client.delete(
        f"/cdn/games/{game.id}/files/00000000-0000-0000-0000-000000000000",
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 404, resp.text


@pytest.mark.asyncio
async def test_delete_foreign_game_file_forbidden(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
):
    game = await create_game(
        author=author, name="draft delete forbidden", dao=GameCreatorImpl(dao)
    )
    guid = await upload(client, game.id, auth_cookies(auth, author))

    # harry is not the author of `game`
    resp = await client.delete(
        f"/cdn/games/{game.id}/files/{guid}",
        cookies=auth_cookies(auth, harry),
    )
    assert resp.status_code == 422, resp.text
    assert (await check_dao.file_info.get_by_guid(guid)).guid == guid
