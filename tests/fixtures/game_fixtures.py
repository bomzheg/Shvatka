import asyncio
from datetime import datetime

import pytest_asyncio
from dataclass_factory import Factory

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto, enums
from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.models.enums.played import Played
from shvatka.core.services.game import upsert_game
from shvatka.core.services.player import join_team
from shvatka.core.services.waiver import add_vote, approve_waivers
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao


@pytest_asyncio.fixture
async def game(
    complex_scn: RawGameScenario,
    author: dto.Player,
    dao: HolderDao,
    dcf: Factory,
    file_gateway: FileGateway,
) -> dto.FullGame:
    return await upsert_game(
        complex_scn,
        author,
        dao.game_upserter,
        dcf,
        file_gateway,
    )


@pytest_asyncio.fixture
async def started_game(
    game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
    harry: dto.Player,
    ron: dto.Player,
    hermione: dto.Player,
    draco: dto.Player,
    dao: HolderDao,
) -> dto.FullGame:
    await join_team(ron, gryffindor, harry, dao.team_player)
    await join_team(hermione, gryffindor, harry, dao.team_player)
    await dao.game.start_waivers(game)

    await add_vote(game, gryffindor, harry, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, hermione, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, ron, Played.no, dao.waiver_vote_adder)
    await add_vote(game, slytherin, draco, Played.yes, dao.waiver_vote_adder)
    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    await dao.game.set_started(game)
    await dao.game.set_start_at(game, datetime.now(tz=tz_utc))
    await dao.level_time.set_to_level(team=gryffindor, game=game, level_number=0)
    await dao.level_time.set_to_level(team=slytherin, game=game, level_number=0)
    await dao.commit()
    return game


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
) -> dto.FullGame:
    game = started_game
    await dao.key_time.save_key(
        key="SHWRONG",
        team=gryffindor,
        level=game.levels[0],
        game=game,
        player=ron,
        type_=enums.KeyType.wrong,
        is_duplicate=False,
    )
    await dao.key_time.save_key(
        key="SH123",
        team=gryffindor,
        level=game.levels[0],
        game=game,
        player=harry,
        type_=enums.KeyType.simple,
        is_duplicate=False,
    )
    await dao.key_time.save_key(
        key="SH123",
        team=slytherin,
        level=game.levels[0],
        game=game,
        player=draco,
        type_=enums.KeyType.simple,
        is_duplicate=False,
    )
    await dao.key_time.save_key(
        key="SH123",
        team=gryffindor,
        level=game.levels[0],
        game=game,
        player=hermione,
        type_=enums.KeyType.simple,
        is_duplicate=True,
    )
    await dao.key_time.save_key(
        key="SH321",
        team=slytherin,
        level=game.levels[0],
        game=game,
        player=draco,
        type_=enums.KeyType.simple,
        is_duplicate=False,
    )
    await dao.game_player.level_up(slytherin, game.levels[0], game)
    await asyncio.sleep(0.1)
    await dao.key_time.save_key(
        key="SH123",
        team=gryffindor,
        level=game.levels[0],
        game=game,
        player=ron,
        type_=enums.KeyType.simple,
        is_duplicate=False,
    )
    await dao.game_player.level_up(gryffindor, game.levels[0], game)
    await asyncio.sleep(0.2)
    await dao.key_time.save_key(
        key="SHOOT",
        team=gryffindor,
        level=game.levels[1],
        game=game,
        player=hermione,
        type_=enums.KeyType.simple,
        is_duplicate=False,
    )
    await dao.game_player.level_up(gryffindor, game.levels[1], game)
    await asyncio.sleep(0.1)
    await dao.key_time.save_key(
        key="SHOOT",
        team=slytherin,
        level=game.levels[1],
        game=game,
        player=draco,
        type_=enums.KeyType.simple,
        is_duplicate=False,
    )
    await dao.game_player.level_up(slytherin, game.levels[1], game)
    await dao.game.set_finished(game)
    await dao.commit()

    return game
