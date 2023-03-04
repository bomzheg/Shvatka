import pytest
from dataclass_factory import Factory
from httpx import AsyncClient

from src.api.models import responses
from src.infrastructure.db.dao.holder import HolderDao
from src.core.models import dto
from src.core.models.enums import GameStatus


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
