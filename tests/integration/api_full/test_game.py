import pytest
from dataclass_factory import Factory
from httpx import AsyncClient

from api.models import responses
from infrastructure.db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums import GameStatus


@pytest.mark.asyncio
async def test_game(game: dto.FullGame, dao: HolderDao, client: AsyncClient):
    await dao.game.start_waivers(game)
    await dao.commit()
    resp = await client.get("/games/active")
    assert resp.is_success
    resp.read()

    dcf = Factory()
    actual = dcf.load(resp.json(), responses.Game)
    assert game.id == actual.id
    assert actual.status == GameStatus.getting_waivers
