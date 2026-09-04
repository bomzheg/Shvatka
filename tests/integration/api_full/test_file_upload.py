import pytest
from httpx import AsyncClient
from sqlalchemy.exc import NoResultFound

from shvatka.api.app.dependencies.auth import AuthProperties
from shvatka.core.models import dto
from shvatka.core.services.game import create_game
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.mocks.file_gateway import FakeTelegram


def auth_cookies(auth: AuthProperties, player: dto.Player) -> dict[str, str]:
    return {"Authorization": "Bearer " + auth.create_user_token(player).access_token}


async def upload(client: AsyncClient, game_id: int, cookies: dict[str, str], force: bool = False):
    return await client.post(
        f"/cdn/games/{game_id}/files{'?force=true' if force else ''}",
        files={"file": ("note.txt", b"hello world", "text/plain")},
        cookies=cookies,
    )


@pytest.mark.asyncio
async def test_uploaded_file_is_sent_to_telegram(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
    telegram: FakeTelegram,
):
    game = await create_game(author=author, name="draft upload ok", dao=dao.game_creator)

    resp = await upload(client, game.id, auth_cookies(auth, author))

    assert resp.status_code == 200, resp.text
    guid = resp.json()["guid"]
    assert telegram.sent == [guid]
    meta = await check_dao.file_info.get_by_guid(guid)
    assert meta.file_id is not None


@pytest.mark.asyncio
async def test_file_telegram_refuses_is_not_stored(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
    telegram: FakeTelegram,
):
    game = await create_game(author=author, name="draft upload refused", dao=dao.game_creator)
    telegram.refuse = True

    resp = await upload(client, game.id, auth_cookies(auth, author))

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["type"] == "FileRejectedByTelegram"
    # the reason telegram gave is what the author has to act on
    assert telegram.reason in body["description"]
    # nothing was kept: no file of this game exists to be used in a hint
    assert await check_dao.game_file.get_file_ids(game.id) == set()


@pytest.mark.asyncio
async def test_force_keeps_the_file_telegram_refused(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
    telegram: FakeTelegram,
):
    game = await create_game(author=author, name="draft upload forced", dao=dao.game_creator)
    telegram.refuse = True

    resp = await upload(client, game.id, auth_cookies(auth, author), force=True)

    assert resp.status_code == 200, resp.text
    guid = resp.json()["guid"]
    meta = await check_dao.file_info.get_by_guid(guid)
    assert meta.file_id is None
    (file_id,) = await check_dao.file_info.get_ids_by_guids([guid])
    assert await check_dao.game_file.get_file_ids(game.id) == {file_id}


@pytest.mark.asyncio
async def test_refused_upload_leaves_no_half_written_file(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
    telegram: FakeTelegram,
):
    game = await create_game(author=author, name="draft upload rollback", dao=dao.game_creator)
    telegram.refuse = True

    await upload(client, game.id, auth_cookies(auth, author))

    (guid,) = telegram.sent
    with pytest.raises(NoResultFound):
        await check_dao.file_info.get_by_guid(guid)
