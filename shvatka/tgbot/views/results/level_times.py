import typing
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any  # noqa: F401

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import trim_tz
from shvatka.core.utils.exceptions import GameNotFinished


@dataclass
class CellAddress:
    column: int
    row: int

    def shift(self, plus_rows=0, plus_columns=0):
        return {"row": self.row + plus_rows, "column": self.column + plus_columns}


FIRST_TEAM_NAME = CellAddress(1, 3)
GAME_NAME = CellAddress(1, 1)


class LevelTime(typing.NamedTuple):
    level: int
    time: datetime


class LevelTimedelta(typing.NamedTuple):
    level: int
    td: timedelta


class TeamLevels(typing.NamedTuple):
    team: dto.Team
    levels_times: list[LevelTime]
    levels_timedelta: list[LevelTimedelta]


@dataclass
class Results:
    data: list[TeamLevels]


DATETIME_EXCEL_FORMAT = "HH:MM:SS"


def export_results(game: dto.FullGame, game_stat: dto.GameStat, file: typing.Any):
    return export_results_internal(game, to_results(game_stat), file)


def to_results(game_stat: dto.GameStat) -> Results:
    result = []
    for team, lts in game_stat.level_times.items():
        levels_times = [LevelTime(lt.level_number, trim_tz(lt.start_at)) for lt in lts]
        levels_timedelta = []
        for previous, current in zip(levels_times[:-1], levels_times[1:]):  # type: LevelTime, LevelTime
            td = current.time - previous.time
            levels_timedelta.append(LevelTimedelta(current.level, td))
        result.append(TeamLevels(team, levels_times, levels_timedelta))
    return Results(result)


def export_results_internal(game: dto.FullGame, results: Results, file: typing.Any):
    if not (game.is_complete() or game.is_finished()):
        raise GameNotFinished
    wb = Workbook()
    ws = typing.cast(Worksheet, wb.active)
    ws.cell(**GAME_NAME.shift()).value = game.name
    i = 0
    for i, team_level_times in enumerate(results.data):
        cell = ws.cell(**FIRST_TEAM_NAME.shift(i, 0))
        cell.value = team_level_times.team.name

        for j, level_time in enumerate(team_level_times.levels_times, 1):
            if i == 0:
                ws.cell(**FIRST_TEAM_NAME.shift(-1, j)).value = level_time.level

            cell = ws.cell(**FIRST_TEAM_NAME.shift(i, j))
            cell.value = level_time.time
            cell.number_format = DATETIME_EXCEL_FORMAT
    second_part_start = i + 3

    for i, team_level_times in enumerate(results.data, second_part_start):
        cell = ws.cell(**FIRST_TEAM_NAME.shift(i, 0))
        cell.value = team_level_times.team.name

        for j, level_td in enumerate(team_level_times.levels_timedelta, 1):
            if i == second_part_start:
                ws.cell(**FIRST_TEAM_NAME.shift(second_part_start - 1, j)).value = level_td.level

            cell = ws.cell(**FIRST_TEAM_NAME.shift(i, j))
            cell.value = as_time(level_td.td)
            cell.number_format = DATETIME_EXCEL_FORMAT

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
