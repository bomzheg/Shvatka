import pytest

from db import models
from db.dao.holder import HolderDao
from shvatka.models.enums.played import Played
from shvatka.services.game import create_game, start_waivers
from shvatka.services.player import join_team, leave
from shvatka.services.waiver import get_vote_to_voted, add_vote, approve_waivers
from shvatka.utils.exceptions import PlayerRestoredInTeam, WaiverForbidden
from tests.utils.player import create_hermi_player, create_harry_player
from tests.utils.team import create_first_team


@pytest.mark.asyncio
async def test_get_voted_list(dao: HolderDao):
    captain = await create_harry_player(dao)
    await dao.player.promote(captain, captain)
    await dao.commit()
    captain.can_be_author = True
    team = await create_first_team(captain, dao)
    player = await create_hermi_player(dao)
    game = await create_game(captain, "good_game", dao.game)
    await start_waivers(game, captain, dao.game)

    await join_team(player, team, dao.player_in_team)
    await add_vote(game, team, captain, Played.yes, dao.waiver_vote_adder)
    await add_vote(game, team, player, Played.yes, dao.waiver_vote_adder)

    actual = await get_vote_to_voted(team, dao.waiver_vote_getter)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 2

    await approve_waivers(game, team, captain, dao.waiver_approver)
    assert 2 == await dao.waiver.count()
    assert [team] == await dao.waiver.get_played_teams(game)

    await leave(player, dao.team_leaver)
    actual = await get_vote_to_voted(team, dao.waiver_vote_getter)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 1
    assert actual_voted[0].player.id == captain.id

    await approve_waivers(game, team, captain, dao.waiver_approver)
    assert 1 == await dao.waiver.count()
    assert [team] == await dao.waiver.get_played_teams(game)

    with pytest.raises(PlayerRestoredInTeam):
        await join_team(player, team, dao.player_in_team)
    await approve_waivers(game, team, captain, dao.waiver_approver)
    # vote not restored after restored player in team
    assert 1 == await dao.waiver.count()

    waiver = models.Waiver(
        player_id=player.id,
        team_id=team.id,
        game_id=game.id,
        role="123",
        played=Played.revoked,
    )
    dao.waiver._save(waiver)
    await dao.waiver.commit()
    with pytest.raises(WaiverForbidden):
        await add_vote(game, team, player, Played.yes, dao.waiver_vote_adder)

    await approve_waivers(game, team, captain, dao.waiver_approver)
    assert 2 == await dao.waiver.count()
    assert [team] == await dao.waiver.get_played_teams(game)
