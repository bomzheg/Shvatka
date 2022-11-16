import operator
from itertools import starmap, pairwise

import pytest

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game_stat import get_game_stat, get_typed_keys


@pytest.mark.asyncio
async def test_game_level_times(completed_game: dto.FullGame, dao: HolderDao):
    game_stat = await get_game_stat(completed_game, dao.game_stat)
    for team, level_times in game_stat.level_times.items():
        assert all(team.id == lt.team.id for lt in level_times)
        assert all(starmap(operator.lt, pairwise(map(lambda lt: lt.level_number, level_times))))


@pytest.mark.asyncio
async def test_game_log_keys(completed_game: dto.FullGame, gryffindor: dto.Team, slytherin: dto.Team, dao: HolderDao):
    actual = await get_typed_keys(completed_game, dao.key_time)
    assert 5 == len(actual[gryffindor])
    assert 3 == len(actual[slytherin])
