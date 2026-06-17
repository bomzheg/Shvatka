from datetime import datetime, timedelta

import pytest
from adaptix import Retort
from httpx import AsyncClient

from shvatka.api.dependencies.auth import AuthProperties
from shvatka.api.models import responses
from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus
from shvatka.core.services.game import create_game
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.scn_fixtures import GUID

# Scenario body for PUT /games/my/{id}/scenario — snake_case (same casing in and out).
SNAKE_SCENARIO: dict = {
    "name": "scenario via api",
    "__model_version__": 1,
    "files": [],
    "levels": [
        {
            "id": "first",
            "__model_version__": 1,
            "conditions": [{"type": "WIN_KEY", "keys": ["SH123", "SH321"]}],
            "time_hints": [
                {"time": 0, "hint": [{"type": "text", "text": "загадка"}]},
                {"time": 5, "hint": [{"type": "text", "text": "подсказка"}]},
            ],
        },
        {
            "id": "second",
            "__model_version__": 1,
            "conditions": [{"type": "WIN_KEY", "keys": ["SHOOT"]}],
            "time_hints": [
                {"time": 0, "hint": [{"type": "text", "text": "загадка два"}]},
            ],
        },
    ],
}


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
    # the `game` fixture references one file (deduplicated across hints)
    assert body["files"] == [
        {
            "guid": GUID,
            "original_filename": "hint2",
            "extension": ".jpg",
            "content_type": "photo",
            "mime_type": None,
        }
    ]


@pytest.mark.asyncio
async def test_scenario_files_round_trip(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
):
    game = await create_game(author=author, name="draft with file ref", dao=dao.game_creator)
    cookies = auth_cookies(auth, author)
    # upload a file and reference it from a hint
    up = await client.post(
        f"/cdn/games/{game.id}/files",
        files={"file": ("pic.png", b"\x89PNG\r\n\x1a\n binary", "image/png")},
        cookies=cookies,
    )
    assert up.status_code == 200, up.text
    f = up.json()
    scenario = {
        "name": "with files",
        "__model_version__": 1,
        "files": [
            {
                "guid": f["guid"],
                "original_filename": f["original_filename"],
                "extension": f["extension"],
            }
        ],
        "levels": [
            {
                "id": "first",
                "__model_version__": 1,
                "conditions": [{"type": "WIN_KEY", "keys": ["SH123"]}],
                "time_hints": [
                    {
                        "time": 0,
                        "hint": [{"type": "photo", "file_guid": f["guid"], "caption": "pic"}],
                    }
                ],
            }
        ],
    }
    expected_files = [
        {
            "guid": f["guid"],
            "original_filename": f["original_filename"],
            "extension": f["extension"],
            "content_type": f["content_type"],
            "mime_type": f["mime_type"],
        }
    ]
    put = await client.put(f"/games/my/{game.id}/scenario", json=scenario, cookies=cookies)
    assert put.status_code == 200, put.text
    assert put.json()["files"] == expected_files
    # and the GET reflects the same files section
    got = await client.get(f"/games/my/{game.id}", cookies=cookies)
    assert got.status_code == 200, got.text
    assert got.json()["files"] == expected_files


@pytest.mark.asyncio
async def test_change_scenario(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    dao: HolderDao,
    retort: Retort,
):
    game = await create_game(author=author, name="draft to fill", dao=dao.game_creator)
    resp = await client.put(
        f"/games/my/{game.id}/scenario",
        json=SNAKE_SCENARIO,
        cookies=auth_cookies(auth, author),
    )
    assert resp.status_code == 200, resp.text
    actual = retort.load(resp.json(), responses.FullGame)
    assert actual.id == game.id
    assert actual.name == SNAKE_SCENARIO["name"]
    assert len(actual.levels) == len(SNAKE_SCENARIO["levels"])
    # response scenario must be the same snake_case shape that was sent in
    assert "time_hints" in actual.levels[0].scenario
    stored = await dao.game.get_full(game.id)
    assert stored.name == SNAKE_SCENARIO["name"]
    assert len(stored.levels) == len(SNAKE_SCENARIO["levels"])


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
):
    # harry is not the author of `game`
    resp = await client.put(
        f"/games/my/{game.id}/scenario",
        json=SNAKE_SCENARIO,
        cookies=auth_cookies(auth, harry),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["type"] == "GameHasAnotherAuthor"
