import dataclasses
from datetime import datetime, time, timedelta

import pytest

from shvatka.common.data_examples import GAME_START_EXAMPLE, game_example
from shvatka.core.games.results import (
    SHORT_HEADER_ROW,
    SHORT_PLACE_COLUMN,
    SHORT_TEAM_COLUMN,
    SHORT_TOTAL_TITLE,
    build_short_results_table,
    build_standings,
)
from shvatka.core.interfaces.printer import CellAddress, CellStyle, Table
from shvatka.core.models import dto, enums
from shvatka.core.utils.datetime_utils import trim_tz
from shvatka.core.utils.exceptions import GameNotFinished

WINNER = dto.Team(id=1, name="Gryffindor", captain=None, is_dummy=False, description=None)
SECOND = dto.Team(id=2, name="Slytherin", captain=None, is_dummy=False, description=None)
LOSER = dto.Team(id=3, name="Hufflepuff", captain=None, is_dummy=False, description=None)

LEVELS_COUNT = len(game_example.levels)
TOTAL_COLUMN = SHORT_TEAM_COLUMN + LEVELS_COUNT + 1


@pytest.fixture
def game_stat() -> dto.GameStat:
    """Two teams finished, the third gave up on the third level."""
    return dto.GameStat(
        level_times={
            LOSER: _level_times(LOSER, {0: 0, 1: 40, 2: 80}),
            WINNER: _level_times(WINNER, {0: 0, 1: 30, 2: 60, 3: 90, 4: 120}),
            SECOND: _level_times(SECOND, {0: 0, 1: 20, 2: 70, 3: 100, 4: 130}),
        }
    )


def _at(minutes: int) -> datetime:
    """The wall clock of the game — what the table shows, in the timezone it is played in."""
    return trim_tz(GAME_START_EXAMPLE + timedelta(minutes=minutes))


def _level_times(team: dto.Team, offsets: dict[int, int]) -> list[dto.LevelTime]:
    return [
        dto.LevelTime(
            id=team.id * 100 + level_number,
            game=game_example,
            team=team,
            level_number=level_number,
            start_at=GAME_START_EXAMPLE + timedelta(minutes=offset),
        )
        for level_number, offset in offsets.items()
    ]


def test_standings_ordered_by_finish(game_stat: dto.GameStat) -> None:
    standings = build_standings(game_example, game_stat)

    assert [place.team for place in standings] == [WINNER, SECOND, LOSER]
    assert [place.levels_taken for place in standings] == [4, 4, 2]
    assert standings[0].finished_at == _at(120)
    assert standings[-1].finished_at is None


def test_standings_keep_the_first_take_of_a_level() -> None:
    """A level entered twice was taken when it was taken first."""
    takes = _level_times(WINNER, {1: 30}) + _level_times(WINNER, {1: 10})
    stat = dto.GameStat(level_times={WINNER: takes})

    (place,) = build_standings(game_example, stat)

    assert place.takes == {1: _at(10)}


def test_short_table_header(game_stat: dto.GameStat) -> None:
    table = build_short_results_table(game_example, game_stat)

    assert _row(table, SHORT_HEADER_ROW) == ["#", "Команда", 1, 2, 3, 4, SHORT_TOTAL_TITLE]


def test_short_table_row_per_team(game_stat: dto.GameStat) -> None:
    table = build_short_results_table(game_example, game_stat)

    assert _row(table, SHORT_HEADER_ROW + 1) == [
        1,
        "Gryffindor",
        _at(30),
        _at(60),
        _at(90),
        _at(120),
        time(2, 0),
    ]


def test_short_table_leaves_what_was_not_taken_empty(game_stat: dto.GameStat) -> None:
    table = build_short_results_table(game_example, game_stat)

    assert _row(table, SHORT_HEADER_ROW + 3) == [
        3,
        "Hufflepuff",
        _at(40),
        _at(80),
        None,
        None,
        None,
    ]


def test_short_table_marks_the_fastest_of_a_level(game_stat: dto.GameStat) -> None:
    table = build_short_results_table(game_example, game_stat)
    first_level_column = SHORT_TEAM_COLUMN + 1

    styles = {
        table.fields[CellAddress(row=row, column=first_level_column)].style
        for row in range(SHORT_HEADER_ROW + 1, SHORT_HEADER_ROW + 4)
    }
    best_row = next(
        row
        for row in range(SHORT_HEADER_ROW + 1, SHORT_HEADER_ROW + 4)
        if table.fields[CellAddress(row=row, column=first_level_column)].style is CellStyle.BEST
    )

    assert styles == {CellStyle.BEST, CellStyle.DATA}
    # the second team took the first level faster than the one that won the game
    assert table.fields[CellAddress(row=best_row, column=SHORT_TEAM_COLUMN)].value == "Slytherin"


def test_short_table_of_unfinished_game(game_stat: dto.GameStat) -> None:
    started = dataclasses.replace(game_example, status=enums.GameStatus.started)

    with pytest.raises(GameNotFinished):
        build_short_results_table(started, game_stat)


def _row(table: Table, row: int) -> list:
    columns = range(SHORT_PLACE_COLUMN, TOTAL_COLUMN + 1)
    return [table.fields[CellAddress(row=row, column=column)].value for column in columns]
