from copy import deepcopy

import pytest
from dataclass_factory import Factory
from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.models.dto.scn.game import RawGameScenario
from shvatka.models.enums import GameStatus
from shvatka.services.game import upsert_game, get_authors_games, start_waivers, get_active
from shvatka.services.organizers import get_orgs


@pytest.mark.asyncio
async def test_game_simple(
    author: dto.Player, simple_scn: RawGameScenario, dao: HolderDao, dcf: Factory, file_storage: FileStorage,
):
    game = await upsert_game(simple_scn, author, dao.game_upserter, dcf, file_storage)

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

    another_scn = deepcopy(simple_scn.scn)
    another_scn["levels"].append(another_scn["levels"].pop(0))

    game = await upsert_game(RawGameScenario(scn=another_scn, files={}), author, dao.game_upserter, dcf, file_storage)

    assert await dao.game.count() == 1
    assert await dao.level.count() == 2

    assert game.name == "My new game"
    assert len(game.levels) == 2
    assert 0 == game.levels[0].number_in_game
    assert "second" == game.levels[0].name_id
    assert 1 == game.levels[1].number_in_game
    assert "first" == game.levels[1].name_id

    another_scn = deepcopy(simple_scn.scn)

    another_scn["levels"].pop()

    game = await upsert_game(RawGameScenario(scn=another_scn, files={}), author, dao.game_upserter, dcf, file_storage)

    assert await dao.game.count() == 1
    assert 1 == await dao.organizer.get_orgs_count(game)
    assert author == (await get_orgs(game, dao.organizer))[0].player
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
async def test_game_get_full(
    author: dto.Player, simple_scn: RawGameScenario, dao: HolderDao, dcf: Factory, file_storage: FileStorage,
):
    game_expected = await upsert_game(simple_scn, author, dao.game_upserter, dcf, file_storage)
    game_actual = await dao.game.get_full(game_expected.id)
    assert game_expected == game_actual
