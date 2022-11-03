from copy import deepcopy

import pytest
from dataclass_factory import Factory

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums import GameStatus
from shvatka.services.game import upsert_game, get_authors_games, start_waivers, get_active


@pytest.mark.asyncio
async def test_game_simple(author: dto.Player, simple_scn: dict, dao: HolderDao, dcf: Factory):
    game = await upsert_game(simple_scn, author, dao.game_upserter, dcf)

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

    game = await upsert_game(another_scn, author, dao.game_upserter, dcf)

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

    game = await upsert_game(another_scn, author, dao.game_upserter, dcf)

    assert await dao.game.count() == 1
    assert 1 == await dao.organizer.get_orgs_count(game)
    assert author == (await dao.organizer.get_orgs(game))[0].player
    assert await dao.level.count() == 2

    assert game.name == "My new game"
    assert len(game.levels) == 1
    assert 0 == game.levels[0].number_in_game
    assert "first" == game.levels[0].name_id

    gotten_games = await get_authors_games(author, dao.game)
    assert 1 == len(gotten_games)
    assert game.id == gotten_games[0].id

    await start_waivers(game, author, dao.game)
    active_game = await get_active(dao.game)
    assert GameStatus.getting_waivers == active_game.status
    assert active_game.id == game.id


@pytest.mark.asyncio
async def test_game_get_full(author: dto.Player, simple_scn: dict, dao: HolderDao, dcf: Factory):
    game_expected = await upsert_game(simple_scn, author, dao.game_upserter, dcf)
    game_actual = await dao.game.get_full(game_expected.id)
    assert game_expected == game_actual
