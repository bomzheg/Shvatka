from datetime import timedelta, time


from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import trim_tz
from shvatka.tgbot.views.results.level_times import (
    results_to_table_linear,
    to_results,
    GAME_NAME,
    FIRST_TEAM_NAME,
    results_to_table_routed,
)


def test_to_results(
    finished_game: dto.FullGame, game_stat: dto.GameStat, gryffindor: dto.Team, slytherin: dto.Team
):
    game = finished_game
    table = results_to_table_linear(game, to_results(game_stat)).fields
    assert table[GAME_NAME].value == game.name
    assert table[FIRST_TEAM_NAME.shift(rows=-1, columns=1)].value == 0
    assert table[FIRST_TEAM_NAME.shift(rows=-1, columns=2)].value == 1
    assert table[FIRST_TEAM_NAME.shift(rows=-1, columns=3)].value == 2
    assert table[FIRST_TEAM_NAME].value == gryffindor.name
    base_time = trim_tz(game.start_at)
    assert table[FIRST_TEAM_NAME.shift(columns=1)].value == base_time
    assert table[FIRST_TEAM_NAME.shift(columns=2)].value == base_time + timedelta(minutes=20)
    assert table[FIRST_TEAM_NAME.shift(columns=3)].value == base_time + timedelta(minutes=30)
    assert table[FIRST_TEAM_NAME.shift(rows=1)].value == slytherin.name
    assert table[FIRST_TEAM_NAME.shift(rows=1, columns=1)].value == base_time
    assert table[FIRST_TEAM_NAME.shift(rows=1, columns=2)].value == base_time + timedelta(
        minutes=10
    )
    assert table[FIRST_TEAM_NAME.shift(rows=1, columns=3)].value == base_time + timedelta(
        minutes=40
    )
    assert table[FIRST_TEAM_NAME.shift(rows=3, columns=1)].value == 1
    assert table[FIRST_TEAM_NAME.shift(rows=3, columns=2)].value == 2
    assert table[FIRST_TEAM_NAME.shift(rows=4)].value == gryffindor.name
    assert table[FIRST_TEAM_NAME.shift(rows=4, columns=1)].value == time(minute=20)
    assert table[FIRST_TEAM_NAME.shift(rows=4, columns=2)].value == time(minute=10)
    assert table[FIRST_TEAM_NAME.shift(rows=5)].value == slytherin.name
    assert table[FIRST_TEAM_NAME.shift(rows=5, columns=1)].value == time(minute=10)
    assert table[FIRST_TEAM_NAME.shift(rows=5, columns=2)].value == time(minute=30)


def test_routed_game_to_table(
    routed_game: dto.FullGame,
    routed_game_stat: dto.GameStat,
    gryffindor: dto.Team,
    slytherin: dto.Team,
):
    game = routed_game
    table = results_to_table_routed(game, to_results(routed_game_stat)).fields
    base_time = trim_tz(game.start_at)
    assert table[GAME_NAME].value == game.name
    assert table[FIRST_TEAM_NAME.shift(rows=-1, columns=1)].value == 0
    assert table[FIRST_TEAM_NAME.shift(rows=-1, columns=2)].value == 1
    assert table[FIRST_TEAM_NAME.shift(rows=-1, columns=3)].value == 2
    assert table[FIRST_TEAM_NAME.shift(rows=-1, columns=4)].value == 3
    assert table[FIRST_TEAM_NAME].value == gryffindor.name
    assert table[FIRST_TEAM_NAME.shift(columns=1)].value == base_time
    assert table[FIRST_TEAM_NAME.shift(rows=1, columns=3)].value == base_time + timedelta(
        minutes=10
    )
    assert table[FIRST_TEAM_NAME.shift(rows=1, columns=4)].value == base_time + timedelta(
        minutes=35
    )
    assert table[FIRST_TEAM_NAME.shift(rows=1)].value == slytherin.name
    assert table[FIRST_TEAM_NAME.shift(rows=1, columns=1)].value == base_time
    assert table[FIRST_TEAM_NAME.shift(rows=1, columns=3)].value == base_time + timedelta(
        minutes=20
    )
    assert table[FIRST_TEAM_NAME.shift(rows=1, columns=4)].value == base_time + timedelta(
        minutes=40
    )
