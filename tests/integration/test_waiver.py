import pytest

from db import models
from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums.played import Played
from shvatka.services.game import start_waivers
from shvatka.services.player import join_team, leave
from shvatka.services.waiver import get_vote_to_voted, add_vote, approve_waivers
from shvatka.utils.exceptions import PlayerRestoredInTeam, WaiverForbidden


@pytest.mark.asyncio
async def test_get_voted_list(
    harry: dto.Player, hermione: dto.Player, author: dto.Player, gryffindor: dto.Team, game: dto.FullGame,
    dao: HolderDao,
):
    await start_waivers(game, author, dao.game)

    await join_team(hermione, gryffindor, harry, dao.player_in_team)
    await add_vote(game, gryffindor, harry, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, gryffindor, hermione, Played.yes, dao.waiver_vote_adder)

    actual = await get_vote_to_voted(gryffindor, dao.waiver_vote_getter)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 2

    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    assert 2 == await dao.waiver.count()
    assert [(gryffindor)] == await dao.waiver.get_played_teams(game)

    await leave(hermione, dao.team_leaver)
    actual = await get_vote_to_voted(gryffindor, dao.waiver_vote_getter)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 1
    assert actual_voted[0].player.id == harry.id

    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    assert 1 == await dao.waiver.count()
    assert [gryffindor] == await dao.waiver.get_played_teams(game)

    with pytest.raises(PlayerRestoredInTeam):
        await join_team(hermione, gryffindor, harry, dao.player_in_team)
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
        await add_vote(game, gryffindor, hermione, Played.yes, dao.waiver_vote_adder)

    await approve_waivers(game, gryffindor, harry, dao.waiver_approver)
    assert 2 == await dao.waiver.count()
    assert [(gryffindor)] == await dao.waiver.get_played_teams(game)
