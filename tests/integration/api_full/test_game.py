from datetime import datetime, timedelta

import pytest
from adaptix import Retort
from dataclass_factory import Factory
from httpx import AsyncClient

from shvatka.api.models import responses
from shvatka.common.factory import REQUIRED_GAME_RECIPES
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.core.models.enums import GameStatus
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db import models
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.api.dependencies.auth import AuthProperties
from tests.fixtures.scn_fixtures import GUID, GUID_2


@pytest.mark.asyncio
async def test_active_game(game: dto.FullGame, dao: HolderDao, client: AsyncClient):
    await dao.game.start_waivers(game)
    await dao.commit()
    resp = await client.get("/games/active")
    assert resp.is_success
    resp.read()

    dcf = Factory()
    actual = dcf.load(resp.json(), responses.Game)
    assert game.id == actual.id
    assert actual.status == GameStatus.getting_waivers


@pytest.mark.asyncio
async def test_games_list(finished_game: dto.FullGame, dao: HolderDao, client: AsyncClient):
    await dao.game.set_completed(finished_game)
    await dao.game.set_number(finished_game, 1)
    await dao.commit()
    resp = await client.get("/games")
    assert resp.is_success
    resp.read()

    dcf = Factory()
    actual: responses.Page[responses.Game] = dcf.load(resp.json(), responses.Page[responses.Game])
    assert len(actual.content) == 1
    game = actual.content[0]
    assert game.id == finished_game.id
    assert game.status == GameStatus.complete


@pytest.mark.asyncio
async def test_game_card(
    finished_game: dto.FullGame,
    dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    harry: dto.Player,
):
    token = auth.create_user_token(harry)
    await dao.game.set_completed(finished_game)
    await dao.game.set_number(finished_game, 1)
    await dao.commit()
    resp = await client.get(
        f"/games/{finished_game.id}",
        cookies={"Authorization": "Bearer " + token.access_token},
    )
    assert resp.is_success
    resp.read()

    retort = Retort(
        recipe=[
            *REQUIRED_GAME_RECIPES,
        ]
    )
    actual = retort.load(resp.json(), responses.FullGame)
    assert actual.id == finished_game.id
    assert actual.status == GameStatus.complete
    assert len(actual.levels) == len(finished_game.levels)
    assert [retort.load(lvl.scenario, scn.LevelScenario) for lvl in actual.levels] == [
        lvl.scenario for lvl in finished_game.levels
    ]


@pytest.mark.asyncio
async def test_game_file(
    finished_game: dto.FullGame,
    dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    harry: dto.Player,
):
    token = auth.create_user_token(harry)
    await dao.game.set_completed(finished_game)
    await dao.game.set_number(finished_game, 1)
    await dao.commit()
    resp = await client.get(
        f"/games/{finished_game.id}/files/{GUID}",
        cookies={"Authorization": "Bearer " + token.access_token},
    )
    assert resp.is_success
    assert resp.read() == b"123"


@pytest.mark.asyncio
async def test_game_file_not_accessible(
    finished_game: dto.FullGame,
    dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    harry: dto.Player,
):
    token = auth.create_user_token(harry)
    await dao.game.set_completed(finished_game)
    await dao.game.set_number(finished_game, 1)
    await dao.commit()
    resp = await client.get(
        f"/games/{finished_game.id}/files/{GUID_2}",
        cookies={"Authorization": "Bearer " + token.access_token},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_game_file_game_not_completed(
    game: dto.FullGame,
    dao: HolderDao,
    client: AsyncClient,
    auth: AuthProperties,
    harry: dto.Player,
):
    token = auth.create_user_token(harry)
    resp = await client.get(
        f"/games/{game.id}/files/{GUID}",
        cookies={"Authorization": "Bearer " + token.access_token},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_game_hints(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    gryffindor: dto.Team,
    started_game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await dao.level_time.delete_all()
    level_time = models.LevelTime(
        game_id=started_game.id,
        team_id=gryffindor.id,
        level_number=0,
        start_at=datetime.now(tz=tz_utc) - timedelta(minutes=3),
    )
    dao.level_time._save(level_time)
    await dao.commit()
    token = auth.create_user_token(harry)
    resp = await client.get(
        "/games/running/level/current",
        cookies={"Authorization": "Bearer " + token.access_token},
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["hints"] == [
        {
            "hint": [
                {"link_preview": None, "text": "загадка", "type": "text"},
                {"link_preview": None, "text": "(сложная)", "type": "text"},
            ],
            "time": 0,
        },
        {
            "hint": [
                {
                    "caption": "привет",
                    "file_guid": "a3bc9b96-3bb8-4dbc-b996-ce1015e66e53",
                    "show_caption_above_media": None,
                    "type": "photo",
                }
            ],
            "time": 2,
        },
    ]
    assert resp_json["level_number"] == 0
    assert resp_json["game_id"] == started_game.id
    assert resp_json["level_time_id"] == level_time.id


@pytest.mark.asyncio
async def test_post_wrong_key(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    gryffindor: dto.Team,
    started_game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    token = auth.create_user_token(harry)
    resp = await client.post(
        "/games/running/key",
        json={"text": "SHWRONG"},
        cookies={"Authorization": "Bearer " + token.access_token},
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["text"] == "SHWRONG"
    assert resp_json["effects"] == []
    assert resp_json["at"] is not None
    assert resp_json["game_finished"] is False
    assert resp_json["is_duplicate"] is False
    assert resp_json["wrong"] is True


@pytest.mark.asyncio
async def test_post_bonus_hint_key(
    client: AsyncClient,
    auth: AuthProperties,
    author: dto.Player,
    harry: dto.Player,
    gryffindor: dto.Team,
    started_game: dto.FullGame,
    dao: HolderDao,
    check_dao: HolderDao,
):
    token = auth.create_user_token(harry)
    resp = await client.post(
        "/games/running/key",
        json={"text": "SHBONUSHINT"},
        cookies={"Authorization": "Bearer " + token.access_token},
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["text"] == "SHBONUSHINT"
    assert resp_json["effects"] == [
        {
            "id": "019d16d6-e501-77fd-af89-50893a58b8f5",
            "bonus_minutes": 0.0,
            "hints_": [
                {"latitude": 55.579282598950165, "longitude": 37.910306366539395, "type": "gps"},
                {"link_preview": None, "text": "this is bonus hint", "type": "text"},
            ],
            "level_up": False,
            "next_level": None,
        }
    ]
    assert resp_json["at"] is not None
    assert resp_json["game_finished"] is False
    assert resp_json["is_duplicate"] is False
    assert resp_json["wrong"] is False
