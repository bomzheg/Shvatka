import typing
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any  # noqa: F401

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import trim_tz
from shvatka.core.utils.exceptions import GameNotFinished


@dataclass(kw_only=True, frozen=True)
class CellAddress:
    column: int
    row: int

    def shift(self, plus_rows: int = 0, plus_columns: int = 0) -> "CellAddress":
        return CellAddress(column=self.column + plus_columns, row=self.row + plus_rows)

    def to_dict(self) -> dict[str, int]:
        return {"row": self.row, "column": self.column}


FIRST_TEAM_NAME = CellAddress(column=1, row=3)
GAME_NAME = CellAddress(column=1, row=1)


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


@dataclass(kw_only=True)
class Cell:
    value: str | datetime | int | time
    format: str | None = None


@dataclass(kw_only=True)
class Table:
    fields: dict[CellAddress, Cell]


DATETIME_EXCEL_FORMAT = "HH:MM:SS"


def export_results(game: dto.FullGame, game_stat: dto.GameStat, file: typing.Any) -> None:
    if not (game.is_complete() or game.is_finished()):
        raise GameNotFinished
    if game.is_routed():
        return print_table(results_to_table_linear(game, to_results(game_stat)), file)
    else:
        return print_table(results_to_table_linear(game, to_results(game_stat)), file)


def results_to_table_linear(game: dto.FullGame, results: Results) -> Table:
    table = {GAME_NAME: Cell(value=game.name)}
    for i, team_level_times in enumerate(results.data):
        table[FIRST_TEAM_NAME.shift(plus_rows=i, plus_columns=0)] = Cell(
            value=team_level_times.team.name
        )

        for j, level_id in enumerate(team_level_times.levels_times, 1):
            level_time = team_level_times.get_level_time(level_id)
            if level_time is None:
                continue
            if i == 0:
                table[FIRST_TEAM_NAME.shift(plus_rows=-1, plus_columns=j)] = Cell(
                    value=level_time.level
                )

            table[FIRST_TEAM_NAME.shift(plus_rows=i, plus_columns=j)] = Cell(
                value=level_time.time,
                format=DATETIME_EXCEL_FORMAT,
            )
    second_part_start = i + 3

    for i, team_level_times in enumerate(results.data, second_part_start):
        table[FIRST_TEAM_NAME.shift(plus_rows=i, plus_columns=0)] = Cell(
            value=team_level_times.team.name
        )

        for j, level_id in enumerate(team_level_times.levels_timedelta, 1):
            level_td = team_level_times.get_level_timedelta(level_id)
            if level_td is None:
                continue
            if i == second_part_start:
                plus_rows = second_part_start - 1
                table[FIRST_TEAM_NAME.shift(plus_rows=plus_rows, plus_columns=j)] = Cell(
                    value=level_td.level
                )
            table[FIRST_TEAM_NAME.shift(plus_rows=i, plus_columns=j)] = Cell(
                value=as_time(level_td.td), format=DATETIME_EXCEL_FORMAT
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
            routed_ltd.setdefault(current.level, []).append(LevelTimedelta(current.level, td))
        result.append(TeamLevels(team, routed_lt, routed_ltd))
    return Results(result)


def print_table(table: Table, file: typing.Any) -> None:
    wb = Workbook()
    ws = typing.cast(Worksheet, wb.active)
    for address, cell_ in table.fields.items():
        cell = ws.cell(**address.to_dict())
        cell.value = cell_.value
        if cell_.format is not None:
            cell.number_format = cell_.format
    resize_columns(ws)
    wb.save(file)


def resize_columns(worksheet: Worksheet):
    for col in worksheet.columns:  # type: Any  # =(
        new_len = max([2, *[len(str(cell.value or "")) for cell in col]])
        worksheet.column_dimensions[col[0].column_letter].width = new_len


def as_time(td: timedelta) -> time:
    hours = td.seconds // 3600
    minutes = (td.seconds - hours * 3600) // 60
    seconds = td.seconds - hours * 3600 - minutes * 60
    return time(hours, minutes, seconds, td.microseconds)
