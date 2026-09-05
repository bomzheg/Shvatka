from copy import deepcopy

import pytest
from adaptix import Retort

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto
from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.models.enums import GameStatus
from shvatka.core.services.current_game import CurrentGameProviderImpl
from shvatka.core.services.game import (
    complete_game,
    get_authors_games,
    start_waivers,
    upsert_game,
)
from shvatka.core.services.level import upsert_level
from shvatka.core.services.organizers import get_orgs
from shvatka.core.utils.exceptions import CantEditGame
from shvatka.infrastructure.db.dao.complex.game import GameUpserterImpl
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.identity import MockIdentityProvider


@pytest.mark.asyncio
async def test_game_simple(
    author: dto.Player,
    three_lvl_scn: RawGameScenario,
    dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
):
    game = await upsert_game(three_lvl_scn, author, GameUpserterImpl(dao), retort, file_gateway)

    assert await dao.game.count() == 1
    assert await dao.level.count() == 3

    assert game.id is not None
    assert game.name == "My new game"
    assert game.status == GameStatus.underconstruction
    assert len(game.levels) == 3
    assert game.levels[0].number_in_game == 0
    assert game.levels[0].name_id == "first"
    assert game.levels[1].number_in_game == 1
    assert game.levels[1].name_id == "second"
    assert game.levels[2].number_in_game == 2
    assert game.levels[2].name_id == "third"

    another_scn = deepcopy(three_lvl_scn.scn)
    another_scn["levels"].append(another_scn["levels"].pop(0))

    game = await upsert_game(
        RawGameScenario(scn=another_scn, files={}),
        author,
        GameUpserterImpl(dao),
        retort,
        file_gateway,
    )

    assert await dao.game.count() == 1
    assert await dao.level.count() == 3

    assert game.name == "My new game"
    assert len(game.levels) == 3
    assert game.levels[0].number_in_game == 0
    assert game.levels[0].name_id == "second"
    assert game.levels[1].number_in_game == 1
    assert game.levels[1].name_id == "third"
    assert game.levels[2].number_in_game == 2
    assert game.levels[2].name_id == "first"

    another_scn = deepcopy(three_lvl_scn.scn)

    another_scn["levels"].pop()

    game = await upsert_game(
        RawGameScenario(scn=another_scn, files={}),
        author,
        GameUpserterImpl(dao),
        retort,
        file_gateway,
    )

    assert await dao.game.count() == 1
    assert await dao.organizer.get_orgs_count(game) == 1
    assert author == (await get_orgs(game, dao.organizer))[0].player
    assert await dao.level.count() == 3

    assert game.name == "My new game"
    assert len(game.levels) == 2
    assert game.levels[0].number_in_game == 0
    assert game.levels[0].name_id == "first"
    assert game.levels[1].number_in_game == 1
    assert game.levels[1].name_id == "second"

    gotten_games = await get_authors_games(MockIdentityProvider(player=author), dao.game)
    assert len(gotten_games) == 1
    assert game.id == gotten_games[0].id

    await start_waivers(game, author, dao.game)
    active_game = await CurrentGameProviderImpl(dao=dao.game, waiver_dao=dao.waiver).get_game()
    assert GameStatus.getting_waivers == active_game.status
    assert active_game.id == game.id


@pytest.mark.asyncio
async def test_game_get_full(
    author: dto.Player,
    simple_scn: RawGameScenario,
    dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
):
    game_expected = await upsert_game(
        simple_scn, author, GameUpserterImpl(dao), retort, file_gateway
    )
    game_actual = await dao.game.get_full(game_expected.id)
    assert game_expected == game_actual


@pytest.mark.asyncio
async def test_game_get_preview(
    author: dto.Player,
    simple_scn: RawGameScenario,
    dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
):
    game_expected = await upsert_game(
        simple_scn, author, GameUpserterImpl(dao), retort, file_gateway
    )
    game_actual = await dao.game.get_preview(game_expected.id)
    assert len(game_expected.levels) == game_actual.levels_count
    assert game_expected.id == game_actual.id
    assert game_expected.name == game_actual.name
    assert game_expected.status == game_actual.status
    assert game_expected.author == game_actual.author


@pytest.mark.asyncio
async def test_cant_change_finished(finished_game: dto.FullGame, dao: HolderDao):
    level = finished_game.levels[0]
    with pytest.raises(CantEditGame):
        await upsert_level(finished_game.author, level.scenario, GameUpserterImpl(dao))


@pytest.mark.asyncio
async def test_set_game_completed(
    finished_game: dto.FullGame, dao: HolderDao, check_dao: HolderDao
):
    await complete_game(game=finished_game, dao=dao.game)
    game = await check_dao.game.get_by_id(finished_game.id, finished_game.author)
    assert game.is_complete()
    db_game = await check_dao.game._get_by_id(finished_game.id)
    assert db_game.number == 1
