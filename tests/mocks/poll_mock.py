from mockito import when

from app.dao.redis.pool import PollDao
from app.models.enums.played import Played
from tests.mocks.aiogram_mocks import mock_coro


def mock_poll_get_users_vote(poll: PollDao, team_id: int, result: dict[int, Played]):
    when(poll).get_dict_player_vote(team_id).thenReturn(mock_coro(result))
