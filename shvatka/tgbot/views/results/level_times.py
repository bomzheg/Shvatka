import typing
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any  # noqa: F401

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import trim_tz
from shvatka.core.utils.exceptions import GameNotFinished
from shvatka.infrastructure.printer.table import (
    print_table,
)
from shvatka.core.interfaces.printer import DATETIME_EXCEL_FORMAT, CellAddress, Cell, Table, as_time

FIRST_TEAM_NAME = CellAddress(row=3, column=1)
GAME_NAME = CellAddress(row=1, column=1)


class LevelTime(typing.NamedTuple):
    level: int
    """level number"""
    time: datetime


class LevelTimedelta(typing.NamedTuple):
    level: int
    """level number"""
    td: timedelta


class TeamLevels(typing.NamedTuple):
    team: dto.Team
    levels_times: dict[int, list[LevelTime]]
    levels_timedelta: dict[int, list[LevelTimedelta]]

    def get_level_time(self, level_number: int) -> LevelTime | None:
        min_time = datetime.max
        requested = self.levels_times.get(level_number, [])
        result = None
        for lt in requested:
            if lt.time < min_time:
                min_time = lt.time
                result = lt
        return result

    def get_level_timedelta(self, level_number: int) -> LevelTimedelta | None:
        result: timedelta = sum(
            (ltd.td for ltd in self.levels_timedelta.get(level_number, [])),
            start=timedelta(seconds=0),
        )
        return LevelTimedelta(level=level_number, td=result)


@dataclass
class Results:
    data: list[TeamLevels]
    game_stat: dto.GameStat


def export_results(game: dto.FullGame, game_stat: dto.GameStat, file: typing.Any) -> None:
    if not (game.is_complete() or game.is_finished()):
        raise GameNotFinished
    return print_table(results_to_table_routed(game, to_results(game_stat)), file)


def results_to_table_routed(game: dto.FullGame, results: Results) -> Table:  # noqa: C901
    table = {
        GAME_NAME: Cell(value=game.name),
        FIRST_TEAM_NAME.shift(rows=-1, columns=1): Cell(value=0),
    }
    for level in game.levels:
        assert level.number_in_game is not None
        table[FIRST_TEAM_NAME.shift(rows=-1, columns=level.number_in_game + 2)] = Cell(
            value=level.number_in_game + 1
        )
    i = 0
    for i, team_level_times in enumerate(results.data):
        table[FIRST_TEAM_NAME.shift(rows=i, columns=0)] = Cell(value=team_level_times.team.name)
        for level_number in team_level_times.levels_times:
            level_time = team_level_times.get_level_time(level_number)
            if level_time is None:
                continue
            table[FIRST_TEAM_NAME.shift(rows=i, columns=level_number + 1)] = Cell(
                value=level_time.time, format=DATETIME_EXCEL_FORMAT
            )
    second_part_start = i + 3
    for level in game.levels:
        assert level.number_in_game is not None
        table[
            FIRST_TEAM_NAME.shift(rows=second_part_start - 1, columns=level.number_in_game + 1)
        ] = Cell(value=level.number_in_game + 1)
    for i, team_level_times in enumerate(results.data, second_part_start):
        table[FIRST_TEAM_NAME.shift(rows=i, columns=0)] = Cell(value=team_level_times.team.name)

        for level_id in team_level_times.levels_timedelta:
            ltd = team_level_times.get_level_timedelta(level_id)
            if ltd is None:
                continue
            table[FIRST_TEAM_NAME.shift(rows=i, columns=level_id + 1)] = Cell(
                value=as_time(ltd.td), format=DATETIME_EXCEL_FORMAT
            )

    third_part_start = i + 3
    for i, (team, lts) in enumerate(results.game_stat.level_times.items()):
        table[FIRST_TEAM_NAME.shift(rows=i * 2 + third_part_start)] = Cell(value=team.name)
        for j, lt in enumerate(lts, 1):
            table[FIRST_TEAM_NAME.shift(rows=i * 2 + third_part_start - 1, columns=j)] = Cell(
                value=trim_tz(lt.start_at), format=DATETIME_EXCEL_FORMAT
            )
            table[FIRST_TEAM_NAME.shift(rows=i * 2 + third_part_start, columns=j)] = Cell(
                value=lt.level_number + 1
            )
    return Table(fields=table)


def to_results(game_stat: dto.GameStat) -> Results:
    result = []
    for team, lts in game_stat.level_times.items():
        levels_times = [LevelTime(lt.level_number, trim_tz(lt.start_at)) for lt in lts]
        routed_lt: dict[int, list[LevelTime]] = {}
        for lt in levels_times:
            routed_lt.setdefault(lt.level, []).append(lt)
        routed_ltd: dict[int, list[LevelTimedelta]] = {}
        for previous, current in zip(levels_times[:-1], levels_times[1:]):  # type: LevelTime, LevelTime
            td = current.time - previous.time
            routed_ltd.setdefault(previous.level, []).append(LevelTimedelta(previous.level, td))
        result.append(TeamLevels(team, routed_lt, routed_ltd))
    return Results(data=result, game_stat=game_stat)
