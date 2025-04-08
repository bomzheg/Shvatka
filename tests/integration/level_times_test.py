from datetime import timedelta, time

import pytest

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import trim_tz
from shvatka.tgbot.views.results.level_times import results_to_table_linear, to_results, GAME_NAME, FIRST_TEAM_NAME


@pytest.mark.skip
def test_to_results(finished_game: dto.FullGame, game_stat: dto.GameStat, gryffindor: dto.Team, slytherin: dto.Team):
    table = results_to_table_linear(finished_game, to_results(game_stat)).fields
    assert table[GAME_NAME].value == finished_game.name
    assert table[FIRST_TEAM_NAME.shift(plus_rows=-1, plus_columns=1)].value == 0
    assert table[FIRST_TEAM_NAME.shift(plus_rows=-1, plus_columns=2)].value == 1
    assert table[FIRST_TEAM_NAME].value == gryffindor.name
    base_time = trim_tz(finished_game.start_at)
    assert table[FIRST_TEAM_NAME.shift(plus_columns=1)].value == base_time + timedelta(minutes=20)
    assert table[FIRST_TEAM_NAME.shift(plus_columns=2)].value == base_time + timedelta(minutes=30)
    assert table[FIRST_TEAM_NAME.shift(plus_rows=1)].value == slytherin.name
    assert table[FIRST_TEAM_NAME.shift(plus_rows=1, plus_columns=1)].value == base_time + timedelta(minutes=10)
    assert table[FIRST_TEAM_NAME.shift(plus_rows=1, plus_columns=2)].value == base_time + timedelta(minutes=40)
    assert table[FIRST_TEAM_NAME.shift(plus_rows=3, plus_columns=1)].value == 1
    assert table[FIRST_TEAM_NAME.shift(plus_rows=3, plus_columns=2)].value == 2
    assert table[FIRST_TEAM_NAME.shift(plus_rows=4)].value == gryffindor.name
    assert table[FIRST_TEAM_NAME.shift(plus_rows=4, plus_columns=1)].value == time(minute=20)
    assert table[FIRST_TEAM_NAME.shift(plus_rows=4, plus_columns=2)].value == time(minute=30)
    assert table[FIRST_TEAM_NAME.shift(plus_rows=5)].value == slytherin.name
    assert table[FIRST_TEAM_NAME.shift(plus_rows=5, plus_columns=1)].value == time(minute=10)
    assert table[FIRST_TEAM_NAME.shift(plus_rows=5, plus_columns=2)].value == time(minute=40)
