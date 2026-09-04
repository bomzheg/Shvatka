import typing
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import pairwise

from shvatka.core.games.dto import BonusEvent
from shvatka.core.interfaces.printer import (
    DATETIME_EXCEL_FORMAT,
    Cell,
    CellAddress,
    CellRange,
    CellStyle,
    Chart,
    ChartSeries,
    SeriesKind,
    Table,
    TableBlock,
    as_time,
)
from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import trim_tz
from shvatka.core.utils.exceptions import GameNotFinished

GAME_NAME = CellAddress(row=1, column=1)
LABEL_COLUMN = 1
"""Column of the team names and of every block's caption."""
START_COLUMN = 2
"""Column of the start of the game — hidden, it only lines the blocks up."""
FIRST_TEAM_NAME = CellAddress(row=GAME_NAME.row + 3, column=LABEL_COLUMN)
"""First team of the first block, under the game name and the two header rows."""
BLOCK_GAP_ROWS = 2
BONUSES_TITLE = "Бонусы, мин"
TOTAL_TITLE = "Итого"
START_TITLE = 0
LEVEL_TIMES_TITLE = "Время взятия"
LEVEL_DURATIONS_TITLE = "Время на уровне"
CHRONOLOGY_TITLE = "Хронология"
AVERAGE_TITLE = "Среднее"
CHART_X_TITLE = "Уровень"
CHART_Y_TITLE = "Время на уровне"
CHART_TIME_FORMAT = "[h]:mm"


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
    bonuses: dict[int | None, list[BonusEvent]]
    """Bonuses and penalties routed by level number. The None key means level unknown."""

    def get_level_bonus(self, level_number: int) -> timedelta:
        return sum(
            (be.td for be in self.bonuses.get(level_number, [])),
            start=timedelta(seconds=0),
        )

    def get_total_bonus(self) -> timedelta:
        return sum(
            (be.td for bes in self.bonuses.values() for be in bes),
            start=timedelta(seconds=0),
        )

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


def build_results_table(
    game: dto.FullGame,
    game_stat: dto.GameStat,
    bonuses: dict[int, list[BonusEvent]] | None = None,
) -> Table:
    if not (game.is_complete() or game.is_finished()):
        raise GameNotFinished
    return results_to_table_routed(game, to_results(game_stat, bonuses))


def results_to_table_routed(game: dto.FullGame, results: Results) -> Table:
    results.data.sort(key=lambda team_levels: _result_key(team_levels, len(game.levels)))
    table = {GAME_NAME: Cell(value=game.name, style=CellStyle.TITLE)}
    blocks = []
    first_row = GAME_NAME.row + 1
    row = _add_level_times_part(table, game, results, row=first_row)
    blocks.append(TableBlock(caption=LEVEL_TIMES_TITLE, first_row=first_row, last_row=row))
    first_row = row + BLOCK_GAP_ROWS
    durations = _add_durations_part(table, game, results, row=first_row)
    blocks.append(
        TableBlock(
            caption=LEVEL_DURATIONS_TITLE, first_row=first_row, last_row=durations.average_row
        )
    )
    first_row = durations.average_row + BLOCK_GAP_ROWS
    row = _add_bonuses_part(table, game, results, row=first_row)
    if row >= first_row:  # a game without a single bonus has no block at all
        blocks.append(TableBlock(caption=BONUSES_TITLE, first_row=first_row, last_row=row))
    first_row = row + BLOCK_GAP_ROWS
    row = _add_chronology_part(table, results, row=first_row)
    blocks.append(TableBlock(caption=CHRONOLOGY_TITLE, first_row=first_row, last_row=row))
    return Table(
        fields=table,
        blocks=blocks,
        charts=_build_charts(game, results, durations, anchor_row=row + BLOCK_GAP_ROWS),
        freeze=CellAddress(row=FIRST_TEAM_NAME.row, column=START_COLUMN),
        hidden_columns=[START_COLUMN],
    )


def _result_key(team_levels: TeamLevels, levels_count: int) -> tuple[bool, datetime, int, str]:
    finish = team_levels.get_level_time(levels_count)
    last = max(
        (lt.time for level_times in team_levels.levels_times.values() for lt in level_times),
        default=datetime.max,
    )
    return (
        finish is None,
        finish.time if finish is not None else last,
        -len(team_levels.levels_times),
        team_levels.team.name or "",
    )


@dataclass(frozen=True)
class DurationsBlock:
    names_row: int
    """Row of the level names — what the chart labels its bars with."""
    first_team_row: int
    last_team_row: int
    average_row: int


def _add_levels_header(
    table: dict[CellAddress, Cell],
    game: dto.FullGame,
    row: int,
    caption: str,
) -> int:
    table[CellAddress(row=row, column=LABEL_COLUMN)] = Cell(value=caption, style=CellStyle.SECTION)
    table[CellAddress(row=row + 1, column=START_COLUMN)] = Cell(
        value=START_TITLE, style=CellStyle.HEADER
    )
    for level in game.levels:
        column = _level_column(level.number_in_game)
        table[CellAddress(row=row, column=column)] = Cell(
            value=level.name_id, style=CellStyle.HEADER
        )
        table[CellAddress(row=row + 1, column=column)] = Cell(
            value=level.number_in_game + 1, style=CellStyle.HEADER
        )
    return row + 2


def _level_column(level_number: int) -> int:
    return START_COLUMN + level_number + 1


def _add_level_times_part(
    table: dict[CellAddress, Cell],
    game: dto.FullGame,
    results: Results,
    row: int,
) -> int:
    first_row = _add_levels_header(table, game, row, LEVEL_TIMES_TITLE)
    _fill_grid(
        table,
        CellAddress(row=first_row, column=START_COLUMN),
        rows=len(results.data),
        columns=len(game.levels) + 1,
    )
    best: dict[int, tuple[datetime, int]] = {}
    for i, team_level_times in enumerate(results.data):
        table[CellAddress(row=first_row + i, column=LABEL_COLUMN)] = Cell(
            value=team_level_times.team.name, style=CellStyle.TEAM
        )
        for level_number in team_level_times.levels_times:
            level_time = team_level_times.get_level_time(level_number)
            if level_time is None:
                continue
            column = START_COLUMN + level_number
            table[CellAddress(row=first_row + i, column=column)] = Cell(
                value=level_time.time, format=DATETIME_EXCEL_FORMAT, style=CellStyle.DATA
            )
            _keep_best(best, column, level_time.time, first_row + i)
    _mark_best(table, best)
    return first_row + len(results.data) - 1


def _add_durations_part(
    table: dict[CellAddress, Cell],
    game: dto.FullGame,
    results: Results,
    row: int,
) -> DurationsBlock:
    first_row = _add_levels_header(table, game, row, LEVEL_DURATIONS_TITLE)
    _fill_grid(
        table,
        CellAddress(row=first_row, column=_level_column(0)),
        rows=len(results.data),
        columns=len(game.levels),
    )
    durations: dict[int, list[timedelta]] = {}
    best: dict[int, tuple[timedelta, int]] = {}
    for i, team_level_times in enumerate(results.data):
        table[CellAddress(row=first_row + i, column=LABEL_COLUMN)] = Cell(
            value=team_level_times.team.name, style=CellStyle.TEAM
        )
        for level_id in team_level_times.levels_timedelta:
            ltd = team_level_times.get_level_timedelta(level_id)
            if ltd is None:
                continue
            durations.setdefault(level_id, []).append(ltd.td)
            column = _level_column(level_id)
            table[CellAddress(row=first_row + i, column=column)] = Cell(
                value=as_time(ltd.td), format=DATETIME_EXCEL_FORMAT, style=CellStyle.DATA
            )
            if ltd.td:
                _keep_best(best, column, ltd.td, first_row + i)
    _mark_best(table, best)
    last_team_row = first_row + len(results.data) - 1
    average_row = last_team_row + 1
    _add_averages_row(table, durations, average_row)
    return DurationsBlock(
        names_row=first_row - 2,
        first_team_row=first_row,
        last_team_row=last_team_row,
        average_row=average_row,
    )


def _add_chronology_part(
    table: dict[CellAddress, Cell],
    results: Results,
    row: int,
) -> int:
    table[CellAddress(row=row, column=LABEL_COLUMN)] = Cell(
        value=CHRONOLOGY_TITLE, style=CellStyle.SECTION
    )
    row += 1
    for team, lts in results.game_stat.level_times.items():
        table[CellAddress(row=row, column=LABEL_COLUMN)] = Cell(
            value=team.name, style=CellStyle.TEAM
        )
        for i, lt in enumerate(lts):
            table[CellAddress(row=row, column=START_COLUMN + i)] = Cell(
                value=trim_tz(lt.start_at), format=DATETIME_EXCEL_FORMAT, style=CellStyle.DATA
            )
            table[CellAddress(row=row + 1, column=START_COLUMN + i)] = Cell(
                value=lt.level_number + 1, style=CellStyle.HEADER
            )
        row += 2
    return row - 1


def _fill_grid(
    table: dict[CellAddress, Cell],
    top_left: CellAddress,
    rows: int,
    columns: int,
) -> None:
    for row in range(rows):
        for column in range(columns):
            table[top_left.shift(rows=row, columns=column)] = Cell(
                value=None, style=CellStyle.DATA
            )


_Best = typing.TypeVar("_Best", datetime, timedelta)


def _keep_best(
    best: dict[int, tuple[_Best, int]],
    column: int,
    value: _Best,
    row: int,
) -> None:
    if column not in best or value < best[column][0]:
        best[column] = (value, row)


def _mark_best(table: dict[CellAddress, Cell], best: dict[int, tuple[_Best, int]]) -> None:
    for column, (_, row) in best.items():
        table[CellAddress(row=row, column=column)].style = CellStyle.BEST


def _add_averages_row(
    table: dict[CellAddress, Cell],
    durations: dict[int, list[timedelta]],
    row: int,
) -> None:
    if not durations:
        return
    table[CellAddress(row=row, column=LABEL_COLUMN)] = Cell(
        value=AVERAGE_TITLE, style=CellStyle.ACCENT
    )
    for level_id, tds in durations.items():
        average = sum(tds, start=timedelta(seconds=0)) / len(tds)
        table[CellAddress(row=row, column=_level_column(level_id))] = Cell(
            value=as_time(average), format=DATETIME_EXCEL_FORMAT, style=CellStyle.ACCENT
        )


def _build_charts(
    game: dto.FullGame,
    results: Results,
    durations: DurationsBlock,
    anchor_row: int,
) -> list[Chart]:
    if not game.levels or not results.data:
        return []
    first_column = _level_column(0)
    last_column = _level_column(len(game.levels) - 1)

    def over_levels(row: int) -> CellRange:
        return CellRange(
            start=CellAddress(row=row, column=first_column),
            end=CellAddress(row=row, column=last_column),
        )

    series = [
        ChartSeries(
            title=CellAddress(row=row, column=LABEL_COLUMN),
            value_range=over_levels(row),
        )
        for row in range(durations.first_team_row, durations.last_team_row + 1)
    ]
    series.append(
        ChartSeries(
            title=CellAddress(row=durations.average_row, column=LABEL_COLUMN),
            value_range=over_levels(durations.average_row),
            kind=SeriesKind.LINE,
            accent=True,
        )
    )
    return [
        Chart(
            title=game.name,
            anchor=CellAddress(row=anchor_row, column=START_COLUMN),
            categories=over_levels(durations.names_row),
            series=series,
            x_title=CHART_X_TITLE,
            y_title=CHART_Y_TITLE,
            y_format=CHART_TIME_FORMAT,
        )
    ]


def _add_bonuses_part(
    table: dict[CellAddress, Cell],
    game: dto.FullGame,
    results: Results,
    row: int,
) -> int:
    if not any(team_levels.bonuses for team_levels in results.data):
        return row - BLOCK_GAP_ROWS
    total_column = _level_column(len(game.levels))
    first_row = _add_levels_header(table, game, row, BONUSES_TITLE)
    # the total is a column of its own: its caption goes where the level names are,
    # and the number row under it stays empty rather than ragged
    table[CellAddress(row=first_row - 2, column=total_column)] = Cell(
        value=TOTAL_TITLE, style=CellStyle.HEADER
    )
    table[CellAddress(row=first_row - 1, column=total_column)] = Cell(
        value=None, style=CellStyle.HEADER
    )
    _fill_grid(
        table,
        CellAddress(row=first_row, column=_level_column(0)),
        rows=len(results.data),
        columns=len(game.levels),
    )
    for i, team_levels in enumerate(results.data):
        table[CellAddress(row=first_row + i, column=LABEL_COLUMN)] = Cell(
            value=team_levels.team.name, style=CellStyle.TEAM
        )
        for level_number, bonus_events in team_levels.bonuses.items():
            if level_number is None:
                continue
            table[CellAddress(row=first_row + i, column=_level_column(level_number))] = Cell(
                value=sum(be.minutes for be in bonus_events), style=CellStyle.DATA
            )
        table[CellAddress(row=first_row + i, column=total_column)] = Cell(
            value=team_levels.get_total_bonus().total_seconds() / 60, style=CellStyle.ACCENT
        )
    return first_row + len(results.data) - 1


def to_results(
    game_stat: dto.GameStat,
    bonuses: dict[int, list[BonusEvent]] | None = None,
) -> Results:
    result = []
    bonuses = bonuses or {}
    for team, lts in game_stat.level_times.items():
        levels_times = [LevelTime(lt.level_number, trim_tz(lt.start_at)) for lt in lts]
        routed_lt: dict[int, list[LevelTime]] = {}
        for lt in levels_times:
            routed_lt.setdefault(lt.level, []).append(lt)
        routed_ltd: dict[int, list[LevelTimedelta]] = {}
        for previous, current in pairwise(levels_times):  # type: LevelTime, LevelTime
            td = current.time - previous.time
            routed_ltd.setdefault(previous.level, []).append(LevelTimedelta(previous.level, td))
        result.append(
            TeamLevels(team, routed_lt, routed_ltd, route_bonuses(lts, bonuses.get(team.id, [])))
        )
    return Results(data=result, game_stat=game_stat)


def resolve_bonus_levels(
    level_times: typing.Sequence[dto.LevelTime],
    bonuses: typing.Iterable[BonusEvent],
) -> list[BonusEvent]:
    levels_by_time_id = {lt.id: lt.level_number for lt in level_times}
    result = []
    for bonus in bonuses:
        level_number = (
            levels_by_time_id.get(bonus.level_time_id) if bonus.level_time_id is not None else None
        )
        if level_number is None:
            level_number = _resolve_level_by_time(level_times, bonus.at)
        result.append(bonus.with_level_number(level_number))
    return result


def route_bonuses(
    level_times: typing.Sequence[dto.LevelTime],
    bonuses: typing.Iterable[BonusEvent],
) -> dict[int | None, list[BonusEvent]]:
    routed: dict[int | None, list[BonusEvent]] = {}
    for bonus in resolve_bonus_levels(level_times, bonuses):
        routed.setdefault(bonus.level_number, []).append(bonus)
    return routed


def _resolve_level_by_time(
    level_times: typing.Sequence[dto.LevelTime], at: datetime
) -> int | None:
    ordered = sorted(level_times, key=lambda lt: lt.start_at)
    result = None
    for lt in ordered:
        if lt.start_at > at:
            break
        result = lt.level_number
    return result
