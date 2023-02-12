import asyncio

import pytest_asyncio
from dataclass_factory import Factory

from infrastructure.db.dao.holder import HolderDao
from shvatka.interfaces.clients.file_storage import FileGateway
from shvatka.models import dto
from shvatka.models.dto.scn.game import RawGameScenario
from shvatka.models.enums.played import Played
from shvatka.services.game import upsert_game
from shvatka.services.player import join_team
from shvatka.services.waiver import add_vote, approve_waivers


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
async def finished_game(
    game: dto.FullGame,
    gryffindor: dto.Team,
    slytherin: dto.Team,
    harry: dto.Player,
    ron: dto.Player,
    hermione: dto.Player,
    draco: dto.Player,
    dao: HolderDao,
):
    await join_team(ron, gryffindor, harry, dao.team_player)
    await join_team(hermione, gryffindor, harry, dao.team_player)
    await dao.game.start_waivers(game)

    await add_vote(game, gryffindor, harry, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, hermione, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, ron, Played.no, dao.waiver_vote_adder)
    await add_vote(game, slytherin, draco, Played.yes, dao.waiver_vote_adder)
    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    await dao.game.set_started(game)

    await dao.key_time.save_key(
        key="SHWRONG",
        team=gryffindor,
        level=game.levels[0],
        game=game,
        player=ron,
        is_correct=False,
        is_duplicate=False,
    )
    await dao.key_time.save_key(
        key="SH123",
        team=gryffindor,
        level=game.levels[0],
        game=game,
        player=harry,
        is_correct=True,
        is_duplicate=False,
    )
    await dao.key_time.save_key(
        key="SH123",
        team=slytherin,
        level=game.levels[0],
        game=game,
        player=draco,
        is_correct=True,
        is_duplicate=False,
    )
    await dao.key_time.save_key(
        key="SH123",
        team=gryffindor,
        level=game.levels[0],
        game=game,
        player=hermione,
        is_correct=True,
        is_duplicate=True,
    )
    await dao.key_time.save_key(
        key="SH321",
        team=slytherin,
        level=game.levels[0],
        game=game,
        player=draco,
        is_correct=True,
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
        is_correct=True,
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
        is_correct=True,
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
        is_correct=True,
        is_duplicate=False,
    )
    await dao.game_player.level_up(slytherin, game.levels[1], game)
    await dao.game.set_finished(game)
    await dao.commit()

    return game
