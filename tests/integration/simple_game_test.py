import pytest
from dataclass_factory import Factory

from app.dao.holder import HolderDao
from app.services.game import upsert_game
from app.services.player import upsert_player
from app.services.user import upsert_user
from tests.fixtures.user_constants import create_dto_harry


@pytest.mark.asyncio
async def test_game_simple(simple_scn: dict, dao: HolderDao, dcf: Factory):
    author = await upsert_player(await upsert_user(create_dto_harry(), dao.user), dao.player)
    game = await upsert_game(simple_scn, author, dao, dcf)

    assert await dao.game.count() == 1
    assert await dao.level.count() == 2

    assert game.id is not None
    assert game.name == "My new game"
    assert len(game.levels) == 2
    assert game.levels[0].number_in_game == 0
    assert game.levels[1].number_in_game == 1
