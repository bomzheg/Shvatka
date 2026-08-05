from datetime import timedelta, time


from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import trim_tz
from shvatka.core.games.results import (
    to_results,
    AVERAGE_TITLE,
    GAME_NAME,
    FIRST_TEAM_NAME,
    results_to_table_routed,
)

# Every block is laid out over the same columns: the game start first (hidden), then
# one column per level. Rows are counted from the first team of the first block.
START = 1
"""Column of the game start, relative to FIRST_TEAM_NAME."""
FIRST_LEVEL = 2
"""Column of the first level, relative to FIRST_TEAM_NAME."""
NAMES_ROW = -2
NUMBERS_ROW = -1
DURATIONS_NUMBERS_ROW = 4
DURATIONS_FIRST_TEAM_ROW = 5


def test_to_results(
    finished_game: dto.FullGame, game_stat: dto.GameStat, gryffindor: dto.Team, slytherin: dto.Team
):
    game = finished_game
    table = results_to_table_routed(game, to_results(game_stat)).fields
    assert table[GAME_NAME].value == game.name

    assert table[FIRST_TEAM_NAME.shift(rows=NUMBERS_ROW, columns=START)].value == 0
    assert table[FIRST_TEAM_NAME.shift(rows=NUMBERS_ROW, columns=FIRST_LEVEL)].value == 1
    assert table[FIRST_TEAM_NAME.shift(rows=NUMBERS_ROW, columns=FIRST_LEVEL + 1)].value == 2
    assert (
        table[FIRST_TEAM_NAME.shift(rows=NAMES_ROW, columns=FIRST_LEVEL)].value
        == game.levels[0].name_id
    )
    assert (
        table[FIRST_TEAM_NAME.shift(rows=NAMES_ROW, columns=FIRST_LEVEL + 1)].value
        == game.levels[1].name_id
    )

    assert table[FIRST_TEAM_NAME].value == gryffindor.name
    base_time = trim_tz(game.start_at)
    assert table[FIRST_TEAM_NAME.shift(columns=START)].value == base_time
    assert table[FIRST_TEAM_NAME.shift(columns=FIRST_LEVEL)].value == base_time + timedelta(
        minutes=20
    )
    assert table[FIRST_TEAM_NAME.shift(columns=FIRST_LEVEL + 1)].value == base_time + timedelta(
        minutes=30
    )
    assert table[FIRST_TEAM_NAME.shift(rows=1)].value == slytherin.name
    assert table[FIRST_TEAM_NAME.shift(rows=1, columns=START)].value == base_time
    assert table[
        FIRST_TEAM_NAME.shift(rows=1, columns=FIRST_LEVEL)
    ].value == base_time + timedelta(minutes=10)
    assert table[
        FIRST_TEAM_NAME.shift(rows=1, columns=FIRST_LEVEL + 1)
    ].value == base_time + timedelta(minutes=40)

    # durations sit under the same level columns as the times they were taken from
    assert table[FIRST_TEAM_NAME.shift(rows=DURATIONS_NUMBERS_ROW, columns=FIRST_LEVEL)].value == 1
    assert (
        table[FIRST_TEAM_NAME.shift(rows=DURATIONS_NUMBERS_ROW, columns=FIRST_LEVEL + 1)].value
        == 2
    )
    assert table[FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW)].value == gryffindor.name
    assert table[
        FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW, columns=FIRST_LEVEL)
    ].value == time(minute=20)
    assert table[
        FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW, columns=FIRST_LEVEL + 1)
    ].value == time(minute=10)
    assert table[FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW + 1)].value == slytherin.name
    assert table[
        FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW + 1, columns=FIRST_LEVEL)
    ].value == time(minute=10)
    assert table[
        FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW + 1, columns=FIRST_LEVEL + 1)
    ].value == time(minute=30)

    average_row = DURATIONS_FIRST_TEAM_ROW + 2
    assert table[FIRST_TEAM_NAME.shift(rows=average_row)].value == AVERAGE_TITLE
    assert table[FIRST_TEAM_NAME.shift(rows=average_row, columns=FIRST_LEVEL)].value == time(
        minute=15
    )
    assert table[FIRST_TEAM_NAME.shift(rows=average_row, columns=FIRST_LEVEL + 1)].value == time(
        minute=20
    )


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
    assert table[FIRST_TEAM_NAME.shift(rows=NUMBERS_ROW, columns=START)].value == 0
    assert table[FIRST_TEAM_NAME.shift(rows=NUMBERS_ROW, columns=FIRST_LEVEL)].value == 1
    assert table[FIRST_TEAM_NAME.shift(rows=NUMBERS_ROW, columns=FIRST_LEVEL + 1)].value == 2
    assert table[FIRST_TEAM_NAME.shift(rows=NUMBERS_ROW, columns=FIRST_LEVEL + 2)].value == 3
    assert table[FIRST_TEAM_NAME].value == gryffindor.name
    assert table[FIRST_TEAM_NAME.shift(columns=START)].value == base_time
    assert table[FIRST_TEAM_NAME.shift(columns=FIRST_LEVEL + 1)].value == base_time + timedelta(
        minutes=10
    )
    assert table[FIRST_TEAM_NAME.shift(columns=FIRST_LEVEL + 2)].value == base_time + timedelta(
        minutes=35
    )
    assert table[FIRST_TEAM_NAME.shift(rows=1)].value == slytherin.name
    assert table[FIRST_TEAM_NAME.shift(rows=1, columns=START)].value == base_time
    assert table[
        FIRST_TEAM_NAME.shift(rows=1, columns=FIRST_LEVEL + 1)
    ].value == base_time + timedelta(minutes=20)
    assert table[
        FIRST_TEAM_NAME.shift(rows=1, columns=FIRST_LEVEL + 2)
    ].value == base_time + timedelta(minutes=40)

    assert table[FIRST_TEAM_NAME.shift(rows=DURATIONS_NUMBERS_ROW, columns=FIRST_LEVEL)].value == 1
    assert (
        table[FIRST_TEAM_NAME.shift(rows=DURATIONS_NUMBERS_ROW, columns=FIRST_LEVEL + 1)].value
        == 2
    )
    assert (
        table[FIRST_TEAM_NAME.shift(rows=DURATIONS_NUMBERS_ROW, columns=FIRST_LEVEL + 2)].value
        == 3
    )
    assert table[FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW)].value == gryffindor.name
    assert table[
        FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW, columns=FIRST_LEVEL)
    ].value == time(minute=15)
    assert table[
        FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW, columns=FIRST_LEVEL + 2)
    ].value == time(minute=20)
    assert table[FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW + 1)].value == slytherin.name
    assert table[
        FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW + 1, columns=FIRST_LEVEL)
    ].value == time(minute=20)
    assert table[
        FIRST_TEAM_NAME.shift(rows=DURATIONS_FIRST_TEAM_ROW + 1, columns=FIRST_LEVEL + 2)
    ].value == time(minute=20)

    # chronology: a team's times on its own row, the level numbers on the row under it
    gryffindor_row = 10
    assert table[FIRST_TEAM_NAME.shift(rows=gryffindor_row)].value == gryffindor.name
    assert table[FIRST_TEAM_NAME.shift(rows=gryffindor_row, columns=START)].value == base_time
    assert table[FIRST_TEAM_NAME.shift(rows=gryffindor_row + 1, columns=START)].value == 1
    assert table[
        FIRST_TEAM_NAME.shift(rows=gryffindor_row, columns=START + 1)
    ].value == base_time + timedelta(minutes=10)
    assert table[FIRST_TEAM_NAME.shift(rows=gryffindor_row + 1, columns=START + 1)].value == 3
    assert table[
        FIRST_TEAM_NAME.shift(rows=gryffindor_row, columns=START + 2)
    ].value == base_time + timedelta(minutes=25)
    assert table[FIRST_TEAM_NAME.shift(rows=gryffindor_row + 1, columns=START + 2)].value == 1
    assert table[
        FIRST_TEAM_NAME.shift(rows=gryffindor_row, columns=START + 3)
    ].value == base_time + timedelta(minutes=30)
    assert table[FIRST_TEAM_NAME.shift(rows=gryffindor_row + 1, columns=START + 3)].value == 3
    assert table[
        FIRST_TEAM_NAME.shift(rows=gryffindor_row, columns=START + 4)
    ].value == base_time + timedelta(minutes=35)
    assert table[FIRST_TEAM_NAME.shift(rows=gryffindor_row + 1, columns=START + 4)].value == 4

    slytherin_row = gryffindor_row + 2
    assert table[FIRST_TEAM_NAME.shift(rows=slytherin_row)].value == slytherin.name
    assert table[FIRST_TEAM_NAME.shift(rows=slytherin_row, columns=START)].value == base_time
    assert table[FIRST_TEAM_NAME.shift(rows=slytherin_row + 1, columns=START)].value == 1
    assert table[
        FIRST_TEAM_NAME.shift(rows=slytherin_row, columns=START + 1)
    ].value == base_time + timedelta(minutes=20)
    assert table[FIRST_TEAM_NAME.shift(rows=slytherin_row + 1, columns=START + 1)].value == 3
    assert table[
        FIRST_TEAM_NAME.shift(rows=slytherin_row, columns=START + 2)
    ].value == base_time + timedelta(minutes=40)
    assert table[FIRST_TEAM_NAME.shift(rows=slytherin_row + 1, columns=START + 2)].value == 4
