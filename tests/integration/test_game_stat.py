import operator
from itertools import starmap, pairwise

import pytest

from shvatka.core.models import dto
from shvatka.core.services.game_stat import get_game_stat, get_typed_keys
from shvatka.infrastructure.db.dao.holder import HolderDao


@pytest.mark.asyncio
async def test_game_level_times(finished_game: dto.FullGame, dao: HolderDao):
    game_stat = await get_game_stat(finished_game, finished_game.author, dao.game_stat)
    for team, level_times in game_stat.level_times.items():
        assert all(team.id == lt.team.id for lt in level_times)
        assert all(starmap(operator.lt, pairwise(map(lambda lt: lt.level_number, level_times))))


@pytest.mark.asyncio
async def test_game_log_keys(
    finished_game: dto.FullGame, gryffindor: dto.Team, slytherin: dto.Team, dao: HolderDao
):
    actual = await get_typed_keys(
        game=finished_game, player=finished_game.author, dao=dao.typed_keys
    )
    assert 5 == len(actual[gryffindor])
    assert 3 == len(actual[slytherin])
