import pytest

from app.dao.holder import HolderDao
from app.dao.redis.pool import PollDao
from app.models.enums.played import Played
from app.services.player import join_to_team, leave
from app.services.waiver import get_voted_list
from tests.mocks.poll_mock import mock_poll_get_users_vote
from tests.utils.player import create_hermi_player, create_harry_player
from tests.utils.team import create_first_team


@pytest.mark.asyncio
async def test_get_voted_list(dao: HolderDao, mock_poll_dao: PollDao):
    captain = await create_harry_player(dao)
    team = await create_first_team(captain, dao)
    player = await create_hermi_player(dao)
    await join_to_team(player, team, dao.player_in_team)
    poll_data = {
        captain.id: Played.yes,
        player.id: Played.yes,
    }
    mock_poll_get_users_vote(mock_poll_dao, team.id, poll_data)

    actual = await get_voted_list(team, dao, mock_poll_dao)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 2

    mock_poll_get_users_vote(mock_poll_dao, team.id, poll_data)

    await leave(player, dao.player_in_team)
    actual = await get_voted_list(team, dao, mock_poll_dao)
    assert len(actual) == 1
    actual_voted = actual[Played.yes]
    assert len(actual_voted) == 1
    assert actual_voted[0].player.id == captain.id
