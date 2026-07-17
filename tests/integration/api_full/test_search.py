import pytest
from httpx import AsyncClient

from shvatka.core.models import dto
from shvatka.infrastructure.db.dao.holder import HolderDao


async def complete_game(game: dto.FullGame, dao: HolderDao) -> None:
    await dao.game.set_completed(game)
    await dao.game.set_number(game, 1)
    await dao.commit()


@pytest.mark.asyncio
async def test_search_levels_by_hint_text(
    finished_game: dto.FullGame, dao: HolderDao, client: AsyncClient
):
    await complete_game(finished_game, dao)
    resp = await client.get("/search", params={"query": "загадка"})
    assert resp.is_success
    content = resp.json()["content"]
    level_hits = [c for c in content if c["type"] == "level"]
    assert len(level_hits) == 2

    first = level_hits[0]
    assert first["game_id"] == finished_game.id
    assert first["game_name"] == finished_game.name
    assert first["level_number"] == 0
    assert first["level_name_id"] == "first"
    assert first["found_in"] == "hint"
    assert first["hint_number"] == 0
    assert first["hint_time"] == 0
    assert first["hint_part_number"] == 0
    assert "загадка" in first["snippet"]

    second = level_hits[1]
    assert second["level_name_id"] == "second"
    assert second["hint_time"] == 0


@pytest.mark.asyncio
async def test_search_levels_by_name_id(
    finished_game: dto.FullGame, dao: HolderDao, client: AsyncClient
):
    await complete_game(finished_game, dao)
    resp = await client.get("/search", params={"query": "first", "players": False})
    assert resp.is_success
    content = resp.json()["content"]
    level_hits = [c for c in content if c["type"] == "level"]
    assert len(level_hits) == 1
    assert level_hits[0]["found_in"] == "name_id"
    assert level_hits[0]["level_name_id"] == "first"


@pytest.mark.asyncio
async def test_search_game_by_name(
    finished_game: dto.FullGame, dao: HolderDao, client: AsyncClient
):
    await complete_game(finished_game, dao)
    resp = await client.get("/search", params={"query": "new game"})
    assert resp.is_success
    content = resp.json()["content"]
    game_hits = [c for c in content if c["type"] == "game"]
    assert len(game_hits) == 1
    assert game_hits[0]["game_id"] == finished_game.id
    assert game_hits[0]["game_name"] == finished_game.name
    assert game_hits[0]["game_number"] == 1
    assert "new game" in game_hits[0]["snippet"]


@pytest.mark.asyncio
async def test_search_hides_not_completed_games(
    game: dto.FullGame, dao: HolderDao, client: AsyncClient
):
    resp = await client.get("/search", params={"query": "загадка"})
    assert resp.is_success
    assert resp.json()["content"] == []

    resp = await client.get("/search", params={"query": "new game"})
    assert resp.is_success
    assert resp.json()["content"] == []


@pytest.mark.asyncio
async def test_search_team(gryffindor: dto.Team, client: AsyncClient):
    resp = await client.get("/search", params={"query": "gryffindor"})
    assert resp.is_success
    content = resp.json()["content"]
    team_hits = [c for c in content if c["type"] == "team"]
    assert len(team_hits) == 1
    assert team_hits[0]["team_id"] == gryffindor.id
    assert team_hits[0]["team_name"] == gryffindor.name


@pytest.mark.asyncio
async def test_search_player_by_tg_name(harry: dto.Player, client: AsyncClient):
    resp = await client.get("/search", params={"query": "Potter"})
    assert resp.is_success
    content = resp.json()["content"]
    player_hits = [c for c in content if c["type"] == "player"]
    assert len(player_hits) == 1
    assert player_hits[0]["player_id"] == harry.id
    assert player_hits[0]["found_in"] == "tg_name"
    assert player_hits[0]["snippet"] == "Harry Potter"


@pytest.mark.asyncio
async def test_search_filters(finished_game: dto.FullGame, dao: HolderDao, client: AsyncClient):
    await complete_game(finished_game, dao)
    resp = await client.get("/search", params={"query": "загадка", "levels": False})
    assert resp.is_success
    assert resp.json()["content"] == []

    resp = await client.get(
        "/search",
        params={"query": "загадка", "games": False, "teams": False, "players": False},
    )
    assert resp.is_success
    content = resp.json()["content"]
    assert content
    assert all(c["type"] == "level" for c in content)
