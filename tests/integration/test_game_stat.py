import operator
from datetime import timedelta
from itertools import starmap, pairwise

import pytest

from shvatka.core.models import dto
from shvatka.core.services.game_stat import get_game_stat, get_typed_keys, get_game_spy
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.mocks.datetime_mock import ClockMock


@pytest.mark.asyncio
async def test_game_level_times(finished_game: dto.FullGame, dao: HolderDao):
    game_stat = await get_game_stat(finished_game, finished_game.author, dao.game_stat)
    for team, level_times in game_stat.level_times.items():
        assert all(team.id == lt.team.id for lt in level_times)
        assert all(starmap(operator.lt, pairwise(lt.level_number for lt in level_times)))


@pytest.mark.asyncio
async def test_game_log_keys(
    finished_game: dto.FullGame, gryffindor: dto.Team, slytherin: dto.Team, dao: HolderDao
):
    actual = await get_typed_keys(
        game=finished_game, player=finished_game.author, dao=dao.typed_keys
    )
    assert 5 == len(actual[gryffindor])
    assert 3 == len(actual[slytherin])


@pytest.mark.asyncio
async def test_game_spy(started_game: dto.FullGame, dao: HolderDao, clock: ClockMock):
    clock.add_mock(tz=tz_utc, result=started_game.start_at + timedelta(seconds=10))
    game_stat = await get_game_spy(started_game, started_game.author, dao.game_stat)
    assert len(game_stat) == 2
    for level_time in game_stat:
        assert level_time.hint.number == 0
        assert level_time.hint.time == 0
        assert level_time.is_finished == False
        assert level_time.level_number == 0
