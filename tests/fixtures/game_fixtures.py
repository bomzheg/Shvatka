import asyncio
from datetime import datetime

import pytest_asyncio
from adaptix import Retort

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto, enums
from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.models.enums.played import Played
from shvatka.core.services.game import upsert_game, start_waivers
from shvatka.core.services.key import KeyProcessor
from shvatka.core.services.player import join_team
from shvatka.core.services.waiver import add_vote, approve_waivers
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.db.dao.holder import HolderDao


@pytest_asyncio.fixture
async def game(
    complex_scn: RawGameScenario,
    author: dto.Player,
    dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
) -> dto.FullGame:
    return await upsert_game(
        complex_scn,
        author,
        dao.game_upserter,
        retort,
        file_gateway,
    )


@pytest_asyncio.fixture
async def game_with_waivers(
    game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
    author: dto.Player,
    harry: dto.Player,
    ron: dto.Player,
    hermione: dto.Player,
    draco: dto.Player,
    dao: HolderDao,
):
    return await add_waivers(
        game=game,
        gryffindor=gryffindor,
        slytherin=slytherin,
        author=author,
        harry=harry,
        ron=ron,
        hermione=hermione,
        draco=draco,
        dao=dao,
    )


@pytest_asyncio.fixture
async def started_game(
    game_with_waivers: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
    dao: HolderDao,
) -> dto.FullGame:
    return await set_game_started(game_with_waivers, [gryffindor, slytherin], dao)


@pytest_asyncio.fixture
async def finished_game(
    started_game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
    harry: dto.Player,
    ron: dto.Player,
    hermione: dto.Player,
    draco: dto.Player,
    dao: HolderDao,
    locker: KeyCheckerFactory,
) -> dto.FullGame:
    game = started_game
    key_processor = KeyProcessor(dao=dao.game_player, game=game, locker=locker)
    await key_processor.submit_key(
        key="SHWRONG",
        player=ron,
        team=gryffindor,
    )
    await key_processor.submit_key(
        key="SH123",
        team=gryffindor,
        player=harry,
    )
    await key_processor.submit_key(
        key="SH123",
        team=slytherin,
        player=draco,
    )
    await key_processor.submit_key(
        key="SH123",
        team=gryffindor,
        player=hermione,
    )
    await key_processor.submit_key(
        key="SH321",
        team=slytherin,
        player=draco,
    )
    await dao.game_player.level_up(slytherin, game.levels[0], game, 1)
    await asyncio.sleep(0.1)
    await key_processor.submit_key(
        key="SH123",
        team=gryffindor,
        player=ron,
    )
    await dao.game_player.level_up(gryffindor, game.levels[0], game, 1)
    await asyncio.sleep(0.2)
    await key_processor.submit_key(
        key="SHOOT",
        team=gryffindor,
        player=hermione,
    )
    await dao.game_player.level_up(gryffindor, game.levels[1], game, 2)
    await asyncio.sleep(0.1)
    await key_processor.submit_key(
        key="SHOOT",
        team=slytherin,
        player=draco,
    )
    await dao.game_player.level_up(slytherin, game.levels[1], game, 2)
    await dao.game.set_finished(game)
    await dao.commit()

    return game


@pytest_asyncio.fixture
async def routed_game(
    author: dto.Player,
    routed_scn: RawGameScenario,
    dao: HolderDao,
    file_gateway: FileGateway,
    retort: Retort,
):
    return await upsert_game(routed_scn, author, dao.game_upserter, retort, file_gateway)


@pytest_asyncio.fixture
async def routed_game_with_waivers(
    routed_game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
    author: dto.Player,
    harry: dto.Player,
    ron: dto.Player,
    hermione: dto.Player,
    draco: dto.Player,
    dao: HolderDao,
):
    return await add_waivers(
        game=routed_game,
        gryffindor=gryffindor,
        slytherin=slytherin,
        author=author,
        harry=harry,
        ron=ron,
        hermione=hermione,
        draco=draco,
        dao=dao,
    )


@pytest_asyncio.fixture
async def started_routed_game(
    routed_game_with_waivers: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
    dao: HolderDao,
) -> dto.FullGame:
    return await set_game_started(routed_game_with_waivers, [gryffindor, slytherin], dao)


async def add_waivers(
    game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
    author: dto.Player,
    harry: dto.Player,
    ron: dto.Player,
    hermione: dto.Player,
    draco: dto.Player,
    dao: HolderDao,
) -> dto.FullGame:
    await join_team(hermione, gryffindor, harry, dao.team_player)
    await join_team(ron, gryffindor, harry, dao.team_player)

    await start_waivers(game, author, dao.game)
    await add_vote(game, gryffindor, harry, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, hermione, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, ron, Played.no, dao.waiver_vote_adder)
    await add_vote(game, slytherin, draco, Played.yes, dao.waiver_vote_adder)

    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    await approve_waivers(game, slytherin, draco, dao.waiver_approver)
    return game


async def set_game_started(
    game: dto.FullGame, teams: list[dto.Team], dao: HolderDao
) -> dto.FullGame:
    await dao.game.set_started(game)
    await dao.game.set_start_at(game, datetime.now(tz=tz_utc))
    for team in teams:
        await dao.level_time.set_to_level(team=team, game=game, level_number=0)
    await dao.commit()
    return game
