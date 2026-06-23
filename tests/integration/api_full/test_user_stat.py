import pytest
from httpx import AsyncClient

from shvatka.core.models import dto
from shvatka.core.utils.defaults_constants import CAPTAIN_ROLE
from shvatka.infrastructure.db.dao.holder import HolderDao


@pytest.mark.asyncio
async def test_get_user_stat(
    client: AsyncClient,
    finished_game: dto.FullGame,
    harry: dto.Player,
    gryffindor: dto.Team,
    dao: HolderDao,
):
    await dao.game.set_completed(finished_game)
    await dao.game.set_number(finished_game, 1)
    await dao.commit()

    resp = await client.get(f"/users/{harry.id}/stat")
    assert resp.is_success
    resp.read()
    body = resp.json()

    assert body["id"] == harry.id
    assert body["username"] == harry.username
    # harry typed one correct key (SH123) in the finished game
    assert body["typed_keys_count"] >= 1
    assert body["typed_correct_keys_count"] >= 1

    # team membership history contains gryffindor as captain
    teams = [tp["team"]["id"] for tp in body["team_history"]]
    assert gryffindor.id in teams
    roles = {tp["team"]["id"]: tp["role"] for tp in body["team_history"]}
    assert roles[gryffindor.id] == CAPTAIN_ROLE
    assert body["team_history"][0]["date_joined"] is not None
    assert "date_left" in body["team_history"][0]

    # harry voted "yes", so the finished game is among his played games
    assert finished_game.id in [game["id"] for game in body["played_games"]]


@pytest.mark.asyncio
async def test_get_user_stat_without_games(
    client: AsyncClient,
    hermione: dto.Player,
):
    resp = await client.get(f"/users/{hermione.id}/stat")
    assert resp.is_success
    resp.read()
    body = resp.json()
    assert body["id"] == hermione.id
    assert body["typed_keys_count"] == 0
    assert body["typed_correct_keys_count"] == 0
    assert body["played_games"] == []
    assert body["team_history"] == []
