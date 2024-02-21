import pytest
from dataclass_factory import Factory
from httpx import AsyncClient

from shvatka.api.models import responses
from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.api.dependencies.auth import AuthProperties


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
    user: dto.User,
):
    token = auth.create_user_token(user)
    await dao.game.set_completed(finished_game)
    await dao.game.set_number(finished_game, 1)
    await dao.commit()
    resp = await client.get(
        f"/games/{finished_game.id}",
        cookies={"Authorization": "Bearer " + token.access_token},
    )
    assert resp.is_success
    resp.read()

    dcf = Factory()
    actual = dcf.load(resp.json(), responses.FullGame)
    assert actual.id == finished_game.id
    assert actual.status == GameStatus.complete
    assert len(actual.levels) == len(finished_game.levels)
    assert [lvl.scenario for lvl in actual.levels] == [
        lvl.scenario for lvl in finished_game.levels
    ]
