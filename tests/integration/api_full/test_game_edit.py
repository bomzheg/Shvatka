from datetime import datetime, timedelta

import pytest
from adaptix import Retort
from httpx import AsyncClient

from shvatka.api.dependencies.auth import AuthProperties
from shvatka.api.models import responses
from shvatka.common.factory import REQUIRED_GAME_RECIPES
from shvatka.core.models import dto
from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.models.enums import GameStatus
from shvatka.core.services.game import create_game
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao


def auth_cookies(auth: AuthProperties, player: dto.Player) -> dict[str, str]:
    token = auth.create_user_token(player)
    return {"Authorization": "Bearer " + token.access_token}


@pytest.mark.asyncio
async def test_create_my_game(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
):
    resp = await client.post(
        "/games/my",
        json={"name": "my brand new game"},
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "my brand new game"
    assert body["status"] == GameStatus.underconstruction.value
    stored = await dao.game.get_by_id(body["id"], author)
    assert stored.name == "my brand new game"


@pytest.mark.asyncio
async def test_my_games_list(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
):
    game = await create_game(author=author, name="draft for list", dao=dao.game_creator)
    resp = await client.get("/games/my", cookies=auth_cookies(auth, author))
    assert resp.status_code == 200, resp.text
    ids = [g["id"] for g in resp.json()["content"]]
    assert game.id in ids


@pytest.mark.asyncio
async def test_my_game_full(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    game: dto.FullGame,
):
    resp = await client.get(f"/games/my/{game.id}", cookies=auth_cookies(auth, author))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == game.id
    assert len(body["levels"]) == len(game.levels)


@pytest.mark.asyncio
async def test_change_scenario(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
    simple_scn: RawGameScenario,
):
    game = await create_game(author=author, name="draft to fill", dao=dao.game_creator)
    resp = await client.put(
        f"/games/my/{game.id}/scenario",
        json=simple_scn.scn,
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 200, resp.text
    retort = Retort(recipe=[*REQUIRED_GAME_RECIPES])
    actual = retort.load(resp.json(), responses.FullGame)
    assert actual.id == game.id
    assert actual.name == simple_scn.scn["name"]
    assert len(actual.levels) == len(simple_scn.scn["levels"])
    stored = await dao.game.get_full(game.id)
    assert stored.name == simple_scn.scn["name"]
    assert len(stored.levels) == len(simple_scn.scn["levels"])


@pytest.mark.asyncio
async def test_change_start_at(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
):
    game = await create_game(author=author, name="draft to schedule", dao=dao.game_creator)
    start_at = datetime.now(tz=tz_utc) + timedelta(days=1)
    resp = await client.put(
        f"/games/my/{game.id}/start_at",
        json={"start_at": start_at.isoformat()},
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 200, resp.text
    stored = await dao.game.get_by_id(game.id, author)
    assert stored.start_at is not None
    assert stored.start_at.astimezone(tz_utc) == start_at

    resp = await client.put(
        f"/games/my/{game.id}/start_at",
        json={"start_at": None},
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 200, resp.text
    stored = await dao.game.get_by_id(game.id, author)
    assert stored.start_at is None


@pytest.mark.asyncio
async def test_change_status(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
):
    game = await create_game(author=author, name="draft to publish", dao=dao.game_creator)
    resp = await client.put(
        f"/games/my/{game.id}/status",
        json={"status": GameStatus.getting_waivers.value},
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == GameStatus.getting_waivers.value
    stored = await dao.game.get_by_id(game.id, author)
    assert stored.status == GameStatus.getting_waivers


@pytest.mark.asyncio
async def test_upload_game_file(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
):
    game = await create_game(author=author, name="draft with files", dao=dao.game_creator)
    resp = await client.post(
        f"/cdn/games/{game.id}/files",
        files={"file": ("note.txt", b"hello world", "text/plain")},
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["guid"]
    assert body["original_filename"] == "note"
    assert body["extension"] == ".txt"
    stored = await dao.file_info.get_by_guid(body["guid"])
    assert stored.author_id == author.id


@pytest.mark.asyncio
async def test_change_scenario_foreign_game_forbidden(
    client: AsyncClient,
    auth: AuthProperties,
    harry: dto.Player,
    game: dto.FullGame,
    simple_scn: RawGameScenario,
):
    # harry is not the author of `game`
    resp = await client.put(
        f"/games/my/{game.id}/scenario",
        json=simple_scn.scn,
        cookies=auth_cookies(auth, harry),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "GameHasAnotherAuthor"
