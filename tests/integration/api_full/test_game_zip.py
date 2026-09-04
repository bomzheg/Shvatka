from io import BytesIO
from typing import Any
from zipfile import ZipFile

import pytest
import yaml
from httpx import AsyncClient

from shvatka.api.app.dependencies.auth import AuthProperties
from shvatka.core.models import dto
from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.services.scenario.scn_zip import pack_scn
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.scn_fixtures import GUID
from tests.mocks.file_gateway import FakeTelegram

IMPORTED_GUID = "5f0c2b1a-77c9-4a9f-9a2f-6f1c2d3e4a5b"


def auth_cookies(auth: AuthProperties, player: dto.Player) -> dict[str, str]:
    return {"Authorization": "Bearer " + auth.create_user_token(player).access_token}


def package(name: str) -> bytes:
    scenario: dict[str, Any] = {
        "name": name,
        "__model_version__": 1,
        "files": [
            {
                "guid": IMPORTED_GUID,
                "original_filename": "картинка",
                "extension": ".jpg",
                "content_type": "photo",
            }
        ],
        "levels": [
            {
                "id": "imported-first",
                "__model_version__": 1,
                "conditions": [{"type": "WIN_KEY", "keys": ["SH123"]}],
                "time_hints": [
                    {
                        "time": 0,
                        "hint": [
                            {"type": "text", "text": "загадка"},
                            {"type": "photo", "file_guid": IMPORTED_GUID},
                        ],
                    },
                ],
            },
        ],
    }
    return pack_scn(RawGameScenario(scn=scenario, files={IMPORTED_GUID: BytesIO(b"123")})).read()


async def import_zip(
    client: AsyncClient, cookies: dict[str, str], zip_bytes: bytes, overwrite: bool = False
):
    return await client.post(
        f"/games/my/zip{'?overwrite=true' if overwrite else ''}",
        files={"file": ("scenario.zip", zip_bytes, "application/zip")},
        cookies=cookies,
    )


@pytest.mark.asyncio
async def test_export_game_as_zip(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    game: dto.FullGame,
):
    resp = await client.get(
        f"/games/my/{game.id}/scenario/zip", cookies=auth_cookies(auth, author)
    )

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/zip"
    names = ZipFile(BytesIO(resp.content)).namelist()
    assert "scn.yaml" in names
    assert GUID in names
    # the scenario travels as yaml, so it can be read and fixed by hand
    scenario = yaml.safe_load(ZipFile(BytesIO(resp.content)).read("scn.yaml"))
    assert scenario["name"] == game.name
    assert len(scenario["levels"]) == len(game.levels)


@pytest.mark.asyncio
async def test_import_zip_writes_a_new_game(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    check_dao: HolderDao,
    telegram: FakeTelegram,
):
    resp = await import_zip(client, auth_cookies(auth, author), package("из архива"))

    assert resp.status_code == 200, resp.text
    imported = resp.json()
    assert imported["name"] == "из архива"
    assert [level["name_id"] for level in imported["levels"]] == ["imported-first"]
    # the media came with it, and went to telegram on the way in
    assert telegram.sent == [IMPORTED_GUID]
    (file_id,) = await check_dao.file_info.get_ids_by_guids([IMPORTED_GUID])
    assert await check_dao.game_file.get_file_ids(imported["id"]) == {file_id}


@pytest.mark.asyncio
async def test_import_asks_before_rewriting_a_game_of_that_name(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    check_dao: HolderDao,
):
    cookies = auth_cookies(auth, author)
    first = await import_zip(client, cookies, package("игра из архива"))
    assert first.status_code == 200, first.text

    second = await import_zip(client, cookies, package("игра из архива"))

    assert second.status_code == 409, second.text
    body = second.json()
    assert body["type"] == "GameWouldBeRewritten"
    assert "игра из архива" in body["description"]
    assert await check_dao.game.count() == 1


@pytest.mark.asyncio
async def test_overwrite_rewrites_the_same_game(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    check_dao: HolderDao,
):
    cookies = auth_cookies(auth, author)
    first = await import_zip(client, cookies, package("игра из архива"))
    assert first.status_code == 200, first.text

    second = await import_zip(client, cookies, package("игра из архива"), overwrite=True)

    assert second.status_code == 200, second.text
    assert second.json()["id"] == first.json()["id"]
    assert await check_dao.game.count() == 1


@pytest.mark.asyncio
async def test_import_refuses_a_package_telegram_wont_take(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    check_dao: HolderDao,
    telegram: FakeTelegram,
):
    telegram.refuse = True

    resp = await import_zip(client, auth_cookies(auth, author), package("игра с плохим файлом"))

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["type"] == "FilesCantBeSentToTg"
    # the author is told which file to fix, not just that something failed
    assert "картинка.jpg" in body["description"]
    assert await check_dao.game.count() == 0


@pytest.mark.asyncio
async def test_import_refuses_what_is_not_a_zip(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
):
    resp = await import_zip(client, auth_cookies(auth, author), b"not a zip at all")

    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "ScenarioNotCorrect"


@pytest.mark.asyncio
async def test_exported_package_can_be_imported_back(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    game: dto.FullGame,
    check_dao: HolderDao,
):
    exported = await client.get(
        f"/games/my/{game.id}/scenario/zip", cookies=auth_cookies(auth, author)
    )
    assert exported.status_code == 200, exported.text

    resp = await import_zip(client, auth_cookies(auth, author), exported.content, overwrite=True)

    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == game.id
    assert len(resp.json()["levels"]) == len(game.levels)
    assert await check_dao.game.count() == 1
