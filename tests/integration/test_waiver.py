import pytest

from app.dao.holder import HolderDao
from app.models.enums.played import Played
from app.services.player import join_to_team, leave
from app.services.waiver import get_voted_list, add_vote
from tests.utils.player import create_hermi_player, create_harry_player
from tests.utils.team import create_first_team


@pytest.mark.asyncio
async def test_get_voted_list(dao: HolderDao):
    poll_dao = dao.poll
    captain = await create_harry_player(dao)
    team = await create_first_team(captain, dao)
    player = await create_hermi_player(dao)
    await join_to_team(player, team, dao.player_in_team)
    await add_vote(team, captain, Played.yes, poll_dao)
    await add_vote(team, player, Played.yes, poll_dao)

    actual = await get_voted_list(team, dao, poll_dao)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 2

    await leave(player, dao.player_in_team)
    actual = await get_voted_list(team, dao, poll_dao)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 1
    assert actual_voted[0].player.id == captain.id
