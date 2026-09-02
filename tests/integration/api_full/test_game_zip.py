from io import BytesIO
from zipfile import Path as ZipPath
from zipfile import ZipFile

import pytest
import yaml
from httpx import AsyncClient

from shvatka.api.app.dependencies.auth import AuthProperties
from shvatka.core.models import dto
from shvatka.core.models.dto.scn.game import RawGameScenario  # noqa: F401
from shvatka.core.services.scenario.scn_zip import pack_scn, unpack_scn
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.scn_fixtures import GUID
from tests.mocks.file_gateway import FakeTelegram


def auth_cookies(auth: AuthProperties, player: dto.Player) -> dict[str, str]:
    return {"Authorization": "Bearer " + auth.create_user_token(player).access_token}


def rename(zip_bytes: bytes, name: str) -> bytes:
    """The package names the game, so this is how one is imported as another."""
    with unpack_scn(ZipPath(BytesIO(zip_bytes))).open() as package:  # type: RawGameScenario
        package.scn["name"] = name
        return pack_scn(package).read()


@pytest.mark.asyncio
async def test_export_game_as_zip(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    game: dto.FullGame,
):
    """The package holds the scenario and the media, so a game moves as one file."""
    resp = await client.get(
        f"/games/my/{game.id}/scenario/zip", cookies=auth_cookies(auth, author)
    )

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/zip"
    names = ZipFile(BytesIO(resp.content)).namelist()
    assert "scn.yaml" in names
    assert GUID in names
    with unpack_scn(ZipPath(BytesIO(resp.content))).open() as package:  # type: RawGameScenario
        assert package.scn["name"] == game.name
        assert len(package.scn["levels"]) == len(game.levels)


@pytest.mark.asyncio
async def test_import_zip_writes_a_new_game(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    game: dto.FullGame,
    check_dao: HolderDao,
):
    exported = await client.get(
        f"/games/my/{game.id}/scenario/zip", cookies=auth_cookies(auth, author)
    )
    package = rename(exported.content, "imported from zip")

    resp = await client.post(
        "/games/my/zip",
        files={"file": ("scenario.zip", package, "application/zip")},
        cookies=auth_cookies(auth, author),
    )

    assert resp.status_code == 200, resp.text
    imported = resp.json()
    assert imported["name"] == "imported from zip"
    assert len(imported["levels"]) == len(game.levels)
    assert imported["id"] != game.id
    assert await check_dao.game.count() == 2


@pytest.mark.asyncio
async def test_import_refuses_a_package_telegram_wont_take(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    game: dto.FullGame,
    check_dao: HolderDao,
    telegram: FakeTelegram,
):
    """An import is expected to be correct — there is no forcing one through."""
    exported = await client.get(
        f"/games/my/{game.id}/scenario/zip", cookies=auth_cookies(auth, author)
    )
    package = rename(exported.content, "package telegram refuses")
    telegram.refuse = True

    resp = await client.post(
        "/games/my/zip",
        files={"file": ("scenario.zip", package, "application/zip")},
        cookies=auth_cookies(auth, author),
    )

    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "FilesCantBeSentToTg"
    assert await check_dao.game.count() == 1


@pytest.mark.asyncio
async def test_import_refuses_what_is_not_a_zip(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
):
    resp = await client.post(
        "/games/my/zip",
        files={"file": ("scenario.zip", b"not a zip at all", "application/zip")},
        cookies=auth_cookies(auth, author),
    )

    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "ScenarioNotCorrect"


@pytest.mark.asyncio
async def test_exported_zip_is_yaml_the_import_takes(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    game: dto.FullGame,
):
    """The scenario travels as yaml, so it can be read and fixed by hand."""
    resp = await client.get(
        f"/games/my/{game.id}/scenario/zip", cookies=auth_cookies(auth, author)
    )

    scenario = yaml.safe_load(ZipFile(BytesIO(resp.content)).read("scn.yaml"))
    assert scenario["name"] == game.name
