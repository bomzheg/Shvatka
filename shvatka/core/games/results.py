import typing
from dataclasses import dataclass
from datetime import datetime, timedelta

from shvatka.core.games.dto import BonusEvent
from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import trim_tz
from shvatka.core.utils.exceptions import GameNotFinished
from shvatka.core.interfaces.printer import (
    DATETIME_EXCEL_FORMAT,
    CellAddress,
    CellRange,
    CellStyle,
    Cell,
    Chart,
    ChartSeries,
    SeriesKind,
    Table,
    as_time,
)

FIRST_TEAM_NAME = CellAddress(row=3, column=1)
GAME_NAME = CellAddress(row=1, column=1)
BONUSES_TITLE = "Бонусы, мин"
TOTAL_TITLE = "Итого"
LEVEL_TIMES_TITLE = "Время взятия"
LEVEL_DURATIONS_TITLE = "Время на уровне"
CHRONOLOGY_TITLE = "Хронология"
AVERAGE_TITLE = "Среднее"
CHART_X_TITLE = "Уровень"
CHART_Y_TITLE = "Время на уровне"
CHART_TIME_FORMAT = "[h]:mm"
CHART_GAP_ROWS = 2


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
        """Total bonus for a single level (a penalty is negative)."""
        return sum(
            (be.td for be in self.bonuses.get(level_number, [])),
            start=timedelta(seconds=0),
        )

    def get_total_bonus(self) -> timedelta:
        """Total bonus for the whole game, including events with no resolved level."""
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


def results_to_table_routed(game: dto.FullGame, results: Results) -> Table:  # noqa: C901
    table = {
        GAME_NAME: Cell(value=game.name, style=CellStyle.TITLE),
        FIRST_TEAM_NAME.shift(rows=-1, columns=0): Cell(
            value=LEVEL_TIMES_TITLE, style=CellStyle.SECTION
        ),
        FIRST_TEAM_NAME.shift(rows=-1, columns=1): Cell(value=0, style=CellStyle.HEADER),
    }
    for level in game.levels:
        table[FIRST_TEAM_NAME.shift(rows=-1, columns=level.number_in_game + 2)] = Cell(
            value=level.number_in_game + 1, style=CellStyle.HEADER
        )
    _fill_grid(
        table,
        FIRST_TEAM_NAME.shift(columns=1),
        rows=len(results.data),
        columns=len(game.levels) + 1,
    )
    i = 0
    for i, team_level_times in enumerate(results.data):
        table[FIRST_TEAM_NAME.shift(rows=i, columns=0)] = Cell(
            value=team_level_times.team.name, style=CellStyle.TEAM
        )
        for level_number in team_level_times.levels_times:
            level_time = team_level_times.get_level_time(level_number)
            if level_time is None:
                continue
            table[FIRST_TEAM_NAME.shift(rows=i, columns=level_number + 1)] = Cell(
                value=level_time.time, format=DATETIME_EXCEL_FORMAT, style=CellStyle.DATA
            )
    second_part_start = i + 3
    table[FIRST_TEAM_NAME.shift(rows=second_part_start - 1, columns=0)] = Cell(
        value=LEVEL_DURATIONS_TITLE, style=CellStyle.SECTION
    )
    for level in game.levels:
        table[
            FIRST_TEAM_NAME.shift(rows=second_part_start - 1, columns=level.number_in_game + 1)
        ] = Cell(value=level.number_in_game + 1, style=CellStyle.HEADER)
    _fill_grid(
        table,
        FIRST_TEAM_NAME.shift(rows=second_part_start, columns=1),
        rows=len(results.data),
        columns=len(game.levels),
    )
    durations: dict[int, list[timedelta]] = {}
    for i, team_level_times in enumerate(results.data, second_part_start):
        table[FIRST_TEAM_NAME.shift(rows=i, columns=0)] = Cell(
            value=team_level_times.team.name, style=CellStyle.TEAM
        )

        for level_id in team_level_times.levels_timedelta:
            ltd = team_level_times.get_level_timedelta(level_id)
            if ltd is None:
                continue
            durations.setdefault(level_id, []).append(ltd.td)
            table[FIRST_TEAM_NAME.shift(rows=i, columns=level_id + 1)] = Cell(
                value=as_time(ltd.td), format=DATETIME_EXCEL_FORMAT, style=CellStyle.DATA
            )
    durations_last_row = i
    _mark_best_durations(table, results, second_part_start)
    _add_averages_row(table, durations, row=durations_last_row + 1)

    third_part_start = i + 3
    table[FIRST_TEAM_NAME.shift(rows=third_part_start - 1, columns=0)] = Cell(
        value=CHRONOLOGY_TITLE, style=CellStyle.SECTION
    )
    for i, (team, lts) in enumerate(results.game_stat.level_times.items()):
        table[FIRST_TEAM_NAME.shift(rows=i * 2 + third_part_start)] = Cell(
            value=team.name, style=CellStyle.TEAM
        )
        for j, lt in enumerate(lts, 1):
            table[FIRST_TEAM_NAME.shift(rows=i * 2 + third_part_start - 1, columns=j)] = Cell(
                value=trim_tz(lt.start_at), format=DATETIME_EXCEL_FORMAT, style=CellStyle.DATA
            )
            table[FIRST_TEAM_NAME.shift(rows=i * 2 + third_part_start, columns=j)] = Cell(
                value=lt.level_number + 1, style=CellStyle.HEADER
            )
    last_row = _add_bonuses_part(table, game, results, start_row=i * 2 + third_part_start + 3)
    return Table(
        fields=table,
        charts=_build_charts(
            game,
            results,
            durations_start_row=second_part_start,
            durations_last_row=durations_last_row,
            anchor_row=last_row + CHART_GAP_ROWS,
        ),
        freeze=FIRST_TEAM_NAME.shift(rows=-1, columns=1),
    )


def _fill_grid(
    table: dict[CellAddress, Cell],
    top_left: CellAddress,
    rows: int,
    columns: int,
) -> None:
    """Draw an empty grid, so a team that never took a level still keeps its row intact."""
    for row in range(rows):
        for column in range(columns):
            table[top_left.shift(rows=row, columns=column)] = Cell(
                value=None, style=CellStyle.DATA
            )


def _mark_best_durations(
    table: dict[CellAddress, Cell],
    results: Results,
    start_row: int,
) -> None:
    """Repaint the fastest team of every level, the way the hand-made tables do it."""
    best: dict[int, tuple[timedelta, int]] = {}
    for row, team_level_times in enumerate(results.data, start_row):
        for level_id in team_level_times.levels_timedelta:
            ltd = team_level_times.get_level_timedelta(level_id)
            if ltd is None or not ltd.td:
                continue
            if level_id not in best or ltd.td < best[level_id][0]:
                best[level_id] = (ltd.td, row)
    for level_id, (_, row) in best.items():
        table[FIRST_TEAM_NAME.shift(rows=row, columns=level_id + 1)].style = CellStyle.BEST


def _add_averages_row(
    table: dict[CellAddress, Cell],
    durations: dict[int, list[timedelta]],
    row: int,
) -> None:
    if not durations:
        return
    table[FIRST_TEAM_NAME.shift(rows=row, columns=0)] = Cell(
        value=AVERAGE_TITLE, style=CellStyle.ACCENT
    )
    for level_id, tds in durations.items():
        average = sum(tds, start=timedelta(seconds=0)) / len(tds)
        table[FIRST_TEAM_NAME.shift(rows=row, columns=level_id + 1)] = Cell(
            value=as_time(average), format=DATETIME_EXCEL_FORMAT, style=CellStyle.ACCENT
        )


def _build_charts(
    game: dto.FullGame,
    results: Results,
    durations_start_row: int,
    durations_last_row: int,
    anchor_row: int,
) -> list[Chart]:
    """One bar per team per level, plus the average as a reference line over them."""
    if not game.levels or not results.data:
        return []
    last_column = len(game.levels)
    header_row = durations_start_row - 1
    series = [
        ChartSeries(
            title=FIRST_TEAM_NAME.shift(rows=row, columns=0),
            value_range=CellRange(
                start=FIRST_TEAM_NAME.shift(rows=row, columns=1),
                end=FIRST_TEAM_NAME.shift(rows=row, columns=last_column),
            ),
        )
        for row in range(durations_start_row, durations_last_row + 1)
    ]
    average_row = durations_last_row + 1
    series.append(
        ChartSeries(
            title=FIRST_TEAM_NAME.shift(rows=average_row, columns=0),
            value_range=CellRange(
                start=FIRST_TEAM_NAME.shift(rows=average_row, columns=1),
                end=FIRST_TEAM_NAME.shift(rows=average_row, columns=last_column),
            ),
            kind=SeriesKind.LINE,
            accent=True,
        )
    )
    return [
        Chart(
            title=game.name,
            anchor=FIRST_TEAM_NAME.shift(rows=anchor_row, columns=0),
            categories=CellRange(
                start=FIRST_TEAM_NAME.shift(rows=header_row, columns=1),
                end=FIRST_TEAM_NAME.shift(rows=header_row, columns=last_column),
            ),
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
    start_row: int,
) -> int:
    """Block of bonuses and penalties in minutes: team x level plus a total.

    Adjusted times are not computed — the file carries the raw numbers so they
    can be worked out in Excel itself. Returns the last row the table occupies.
    """
    if not any(team_levels.bonuses for team_levels in results.data):
        return start_row - 3
    total_column = len(game.levels) + 1
    table[FIRST_TEAM_NAME.shift(rows=start_row - 1, columns=0)] = Cell(
        value=BONUSES_TITLE, style=CellStyle.SECTION
    )
    for level in game.levels:
        table[FIRST_TEAM_NAME.shift(rows=start_row - 1, columns=level.number_in_game + 1)] = Cell(
            value=level.number_in_game + 1, style=CellStyle.HEADER
        )
    table[FIRST_TEAM_NAME.shift(rows=start_row - 1, columns=total_column)] = Cell(
        value=TOTAL_TITLE, style=CellStyle.HEADER
    )
    _fill_grid(
        table,
        FIRST_TEAM_NAME.shift(rows=start_row, columns=1),
        rows=len(results.data),
        columns=total_column,
    )
    i = start_row
    for i, team_levels in enumerate(results.data, start_row):
        table[FIRST_TEAM_NAME.shift(rows=i, columns=0)] = Cell(
            value=team_levels.team.name, style=CellStyle.TEAM
        )
        for level_number, bonus_events in team_levels.bonuses.items():
            if level_number is None:
                continue
            table[FIRST_TEAM_NAME.shift(rows=i, columns=level_number + 1)] = Cell(
                value=sum(be.minutes for be in bonus_events), style=CellStyle.DATA
            )
        table[FIRST_TEAM_NAME.shift(rows=i, columns=total_column)] = Cell(
            value=team_levels.get_total_bonus().total_seconds() / 60, style=CellStyle.ACCENT
        )
    return i


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
        for previous, current in zip(levels_times[:-1], levels_times[1:]):  # type: LevelTime, LevelTime
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
    """Set on each bonus the number of the level it was earned on.

    The level comes from the event's ``level_time_id``. When that is missing (the
    column is nullable), the level is resolved by the event's time: the one the
    team was on at ``at``. What cannot be resolved keeps ``level_number=None``
    and only counts towards the total.
    """
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
    """Route a team's bonuses by level number. The None key means level unknown."""
    routed: dict[int | None, list[BonusEvent]] = {}
    for bonus in resolve_bonus_levels(level_times, bonuses):
        routed.setdefault(bonus.level_number, []).append(bonus)
    return routed


def _resolve_level_by_time(
    level_times: typing.Sequence[dto.LevelTime], at: datetime
) -> int | None:
    """Find the level the team was on at ``at``."""
    ordered = sorted(level_times, key=lambda lt: lt.start_at)
    result = None
    for lt in ordered:
        if lt.start_at > at:
            break
        result = lt.level_number
    return result
