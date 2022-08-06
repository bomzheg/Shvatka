from copy import deepcopy

import pytest
from dataclass_factory import Factory

from app.dao.holder import HolderDao
from app.models.enums import GameStatus
from app.services.game import upsert_game
from app.services.player import upsert_player
from app.services.user import upsert_user
from tests.fixtures.user_constants import create_dto_harry


@pytest.mark.asyncio
async def test_game_simple(simple_scn: dict, dao: HolderDao, dcf: Factory):
    author = await upsert_player(await upsert_user(create_dto_harry(), dao.user), dao.player)
    await dao.player.promote(author, author)
    await dao.commit()
    author.can_be_author = True
    game = await upsert_game(simple_scn, author, dao, dcf)

    assert await dao.game.count() == 1
    assert await dao.level.count() == 2

    assert game.id is not None
    assert game.name == "My new game"
    assert game.status == GameStatus.underconstruction
    assert len(game.levels) == 2
    assert 0 == game.levels[0].number_in_game
    assert "first" == game.levels[0].name_id
    assert 1 == game.levels[1].number_in_game
    assert "second" == game.levels[1].name_id

    another_scn = deepcopy(simple_scn)
    another_scn["levels"].append(another_scn["levels"].pop(0))

    game = await upsert_game(another_scn, author, dao, dcf)

    assert await dao.game.count() == 1
    assert await dao.level.count() == 2

    assert game.name == "My new game"
    assert len(game.levels) == 2
    assert 0 == game.levels[0].number_in_game
    assert "second" == game.levels[0].name_id
    assert 1 == game.levels[1].number_in_game
    assert "first" == game.levels[1].name_id

    another_scn = deepcopy(simple_scn)

    another_scn["levels"].pop()

    game = await upsert_game(another_scn, author, dao, dcf)

    assert await dao.game.count() == 1
    assert await dao.level.count() == 2

    assert game.name == "My new game"
    assert len(game.levels) == 1
    assert 0 == game.levels[0].number_in_game
    assert "first" == game.levels[0].name_id
