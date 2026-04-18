import pytest
import pytest_asyncio
from dishka import AsyncContainer

from shvatka.core.models import dto
from shvatka.core.models.enums.played import Played
from shvatka.core.services.game import start_waivers
from shvatka.core.services.player import join_team, leave
from shvatka.core.waiver.services import (
    get_vote_to_voted,
    add_vote,
    approve_waivers,
    get_all_played,
)
from shvatka.core.utils.exceptions import PlayerRestoredInTeam, WaiverForbidden
from shvatka.core.waiver.adapters import WaiverVoteAdder, WaiverVoteGetter
from shvatka.infrastructure.db import models
from shvatka.infrastructure.db.dao.holder import HolderDao


@pytest.mark.asyncio
async def test_get_voted_list(
    harry: dto.Player,
    hermione: dto.Player,
    author: dto.Player,
    gryffindor: dto.Team,
    game: dto.FullGame,
    dao: HolderDao,
    dishka_request: AsyncContainer,
):
    await start_waivers(game, author, dao.game)

    await join_team(hermione, gryffindor, harry, dao.team_player)
    waiver_vote_adder = await dishka_request.get(WaiverVoteAdder)
    await add_vote(game, gryffindor, harry, Played.yes, waiver_vote_adder)
    await add_vote(game, gryffindor, hermione, Played.yes, waiver_vote_adder)

    waiver_vote_getter = await dishka_request.get(WaiverVoteGetter)
    actual = await get_vote_to_voted(gryffindor, waiver_vote_getter)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 2

    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    assert 2 == await dao.waiver.count()
    assert [gryffindor] == await dao.waiver.get_played_teams(game)
    waivers = await get_all_played(game, dao.waiver)
    assert 1 == len(waivers)
    players = list(waivers[gryffindor])
    assert 2 == len(players)
    assert {harry.id, hermione.id} == {player.player.id for player in players}

    await leave(hermione, hermione, dao.team_leaver)
    actual = await get_vote_to_voted(gryffindor, waiver_vote_getter)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 1
    assert actual_voted[0].player.id == harry.id

    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    assert 1 == await dao.waiver.count()
    assert [gryffindor] == await dao.waiver.get_played_teams(game)

    with pytest.raises(PlayerRestoredInTeam):
        await join_team(hermione, gryffindor, harry, dao.team_player)
    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    # vote not restored after restored player in team
    assert 1 == await dao.waiver.count()

    waiver = models.Waiver(
        player_id=hermione.id,
        team_id=gryffindor.id,
        game_id=game.id,
        role="123",
        played=Played.revoked,
    )
    dao.waiver._save(waiver)
    await dao.waiver.commit()
    with pytest.raises(WaiverForbidden):
        await add_vote(game, gryffindor, hermione, Played.yes, waiver_vote_adder)

    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    assert 2 == await dao.waiver.count()
    assert [gryffindor] == await dao.waiver.get_played_teams(game)


@pytest_asyncio.fixture
async def harry_waiver(
    harry: dto.Player,
    gryffindor: dto.Team,
    game: dto.FullGame,
    dao: HolderDao,
):
    waiver = models.Waiver(
        player_id=harry.id,
        team_id=gryffindor.id,
        game_id=game.id,
        role="harry",
        played=Played.yes,
    )
    dao.waiver._save(waiver)
    await dao.waiver.commit()
    return waiver.to_dto(player=harry, team=gryffindor, game=game)


@pytest_asyncio.fixture
async def hermi_waiver(
    hermione: dto.Player,
    harry: dto.Player,
    gryffindor: dto.Team,
    game: dto.FullGame,
    dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player)
    waiver = models.Waiver(
        player_id=hermione.id,
        team_id=gryffindor.id,
        game_id=game.id,
        role="hermione",
        played=Played.yes,
    )
    dao.waiver._save(waiver)
    await dao.waiver.commit()
    return waiver.to_dto(player=hermione, team=gryffindor, game=game)


@pytest_asyncio.fixture
async def ron_waiver(
    ron: dto.Player,
    harry: dto.Player,
    gryffindor: dto.Team,
    game: dto.FullGame,
    dao: HolderDao,
):
    await join_team(ron, gryffindor, harry, dao.team_player)
    waiver = models.Waiver(
        player_id=ron.id,
        team_id=gryffindor.id,
        game_id=game.id,
        role="ron",
        played=Played.no,
    )
    dao.waiver._save(waiver)
    await dao.waiver.commit()
    return waiver.to_dto(player=ron, team=gryffindor, game=game)


@pytest_asyncio.fixture
async def draco_waiver(
    draco: dto.Player,
    slytherin: dto.Team,
    game: dto.FullGame,
    dao: HolderDao,
):
    waiver = models.Waiver(
        player_id=draco.id,
        team_id=slytherin.id,
        game_id=game.id,
        role="draco",
        played=Played.yes,
    )
    dao.waiver._save(waiver)
    await dao.waiver.commit()
    return waiver.to_dto(player=draco, team=slytherin, game=game)


@pytest.mark.asyncio
async def test_waiver_list(
    harry_waiver: dto.Waiver,
    hermi_waiver: dto.Waiver,
    ron_waiver: dto.Waiver,
    draco_waiver: dto.Waiver,
    game: dto.FullGame,
    dao: HolderDao,
):
    assert 4 == await dao.waiver.count()
    waivers = await get_all_played(game, dao.waiver)
    assert 2 == len(waivers)
    slytherin_waivers = waivers.pop(draco_waiver.team)
    gryffindor_waivers = waivers.pop(hermi_waiver.team)
    assert not waivers
    assert {harry_waiver.player.id, hermi_waiver.player.id} == {
        waiver.player.id for waiver in gryffindor_waivers
    }
    assert {draco_waiver.player.id} == {waiver.player.id for waiver in slytherin_waivers}
