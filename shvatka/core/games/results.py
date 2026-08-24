import typing
from dataclasses import dataclass
from datetime import datetime, timedelta

from shvatka.core.games.dto import BonusEvent
from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import trim_tz
from shvatka.core.utils.exceptions import GameNotFinished
from shvatka.core.interfaces.printer import (
    DATETIME_EXCEL_FORMAT,
    TIME_EXCEL_FORMAT,
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


def results_to_table_routed(game: dto.FullGame, results: Results) -> Table:
    """Lay the game out block by block, every block over the same columns.

    Column ``START_COLUMN`` is the start of the game — the same instant for
    every team, so only the chronology has anything to say there. It is kept as
    a column all the same, to line the blocks up, and hidden by default.
    Column ``START_COLUMN + n`` is level ``n`` counted from one.
    """
    table = {GAME_NAME: Cell(value=game.name, style=CellStyle.TITLE)}
    row = _add_level_times_part(table, game, results, row=GAME_NAME.row + 1)
    durations = _add_durations_part(table, game, results, row=row + BLOCK_GAP_ROWS)
    row = _add_bonuses_part(table, game, results, row=durations.average_row + BLOCK_GAP_ROWS)
    row = _add_chronology_part(table, results, row=row + BLOCK_GAP_ROWS)
    return Table(
        fields=table,
        charts=_build_charts(game, results, durations, anchor_row=row + BLOCK_GAP_ROWS),
        freeze=CellAddress(row=FIRST_TEAM_NAME.row, column=START_COLUMN),
        hidden_columns=[START_COLUMN],
    )


@dataclass(frozen=True)
class DurationsBlock:
    """Where the per-level durations landed — the chart is drawn from them."""

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
    """Caption plus a two row header — level name over level number. Returns the first data row."""
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
    """Column of level ``level_number`` (counted from zero) in every block but the chronology."""
    return START_COLUMN + level_number + 1


def _add_level_times_part(
    table: dict[CellAddress, Cell],
    game: dto.FullGame,
    results: Results,
    row: int,
) -> int:
    """When each team took each level. The level after the last one is the finish."""
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
    """How long each team spent on each level, with the fastest marked and an average under it."""
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
    """Every team's levels in the order it took them — the level number under its time."""
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
    """Draw an empty grid, so a team that never took a level still keeps its row intact."""
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
    """Remember the smallest value of a column and the row it is on."""
    if column not in best or value < best[column][0]:
        best[column] = (value, row)


def _mark_best(table: dict[CellAddress, Cell], best: dict[int, tuple[_Best, int]]) -> None:
    """Repaint the leader of every column, the way the hand-made tables do it."""
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
    """One bar per team per level, plus the average as a reference line over them."""
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
    """Block of bonuses and penalties in minutes: team x level plus a total.

    Adjusted times are not computed — the file carries the raw numbers so they
    can be worked out in Excel itself. Returns the last row the table occupies.
    """
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


SHORT_PLACE_TITLE = "#"
SHORT_TEAM_TITLE = "Команда"
SHORT_TOTAL_TITLE = "Итого"
SHORT_PLACE_COLUMN = 1
SHORT_TEAM_COLUMN = 2
SHORT_HEADER_ROW = 1


@dataclass(frozen=True)
class TeamPlace:
    """One line of the standings: what a team took and when it was over for it."""

    team: dto.Team
    takes: dict[int, datetime]
    """When the team took each level, by level number counted from one."""
    finished_at: datetime | None
    """When the team took the last level of the game; None if it never did."""

    @property
    def levels_taken(self) -> int:
        return len(self.takes)

    @property
    def last_take(self) -> datetime | None:
        return max(self.takes.values(), default=None)

    def durations(self, started_at: datetime) -> dict[int, timedelta]:
        """How long the team spent on each level, by level number counted from one.

        A level lasted from taking the one before it (the start of the game, for
        the first) until taking it. A level whose predecessor was never taken is
        left out — there is nothing to measure it from.
        """
        result = {}
        for level_number, at in self.takes.items():
            previous = started_at if level_number == 1 else self.takes.get(level_number - 1)
            if previous is None:
                continue
            result[level_number] = at - previous
        return result


def build_standings(game: dto.FullGame, game_stat: dto.GameStat) -> list[TeamPlace]:
    """Order the teams the way the results are read: who finished first, then who got furthest."""
    levels_count = len(game.levels)
    places = []
    for team, level_times in game_stat.level_times.items():
        takes: dict[int, datetime] = {}
        for level_time in level_times:
            # entering level number n means the team has just taken level n — and
            # entering the first level is the start of the game, taken by nobody
            if level_time.level_number == 0:
                continue
            at = trim_tz(level_time.start_at)
            taken = takes.get(level_time.level_number)
            if taken is None or at < taken:
                takes[level_time.level_number] = at
        # taking the last level of the game is the finish, whatever its number is
        finished = [at for number, at in takes.items() if number >= levels_count]
        places.append(
            TeamPlace(team=team, takes=takes, finished_at=min(finished, default=None)),
        )
    return sorted(places, key=_standings_key)


def _standings_key(place: TeamPlace) -> tuple[bool, datetime, int, datetime, str]:
    return (
        place.finished_at is None,
        place.finished_at or datetime.max,
        -place.levels_taken,
        place.last_take or datetime.max,
        place.team.name or "",
    )


def build_short_results_table(game: dto.FullGame, game_stat: dto.GameStat) -> Table:
    """The standings alone — a row per team, a column per level, no blocks and no charts.

    Short enough to be read in a message, unlike the file the same game exports to.
    """
    started_at = _short_start(game)
    table = _short_header(game, total_title=SHORT_TOTAL_TITLE)
    total_column = _short_total_column(game)
    best: dict[int, tuple[datetime, int]] = {}
    for row, place in _short_rows(table, game, game_stat):
        for level_number in _short_levels(game):
            column = _short_level_column(level_number)
            take = place.takes.get(level_number)
            table[CellAddress(row=row, column=column)] = Cell(
                value=take,
                format=TIME_EXCEL_FORMAT if take is not None else None,
                style=CellStyle.DATA,
            )
            if take is not None:
                _keep_best(best, column, take, row)
        table[CellAddress(row=row, column=total_column)] = Cell(
            value=as_time(place.finished_at - started_at) if place.finished_at else None,
            format=DATETIME_EXCEL_FORMAT if place.finished_at else None,
            style=CellStyle.ACCENT,
        )
    _mark_best(table, best)
    return Table(fields=table)


def build_short_durations_table(game: dto.FullGame, game_stat: dto.GameStat) -> Table:
    """How long every team spent on every level, teams in the order the standings put them.

    The companion of :func:`build_short_results_table`: the same grid, telling
    how long a level took rather than when it was over.
    """
    started_at = _short_start(game)
    table = _short_header(game)
    best: dict[int, tuple[timedelta, int]] = {}
    by_level: dict[int, list[timedelta]] = {}
    last_row = SHORT_HEADER_ROW
    for row, place in _short_rows(table, game, game_stat):
        last_row = row
        durations = place.durations(started_at)
        for level_number in _short_levels(game):
            column = _short_level_column(level_number)
            duration = durations.get(level_number)
            table[CellAddress(row=row, column=column)] = Cell(
                value=as_time(duration) if duration is not None else None,
                format=TIME_EXCEL_FORMAT if duration is not None else None,
                style=CellStyle.DATA,
            )
            if duration:
                by_level.setdefault(level_number, []).append(duration)
                _keep_best(best, column, duration, row)
    _mark_best(table, best)
    _add_short_averages(table, by_level, row=last_row + 1)
    return Table(fields=table)


def _short_start(game: dto.FullGame) -> datetime:
    if not (game.is_complete() or game.is_finished()):
        raise GameNotFinished
    assert game.start_at is not None
    return trim_tz(game.start_at)


def _short_header(game: dto.FullGame, total_title: str | None = None) -> dict[CellAddress, Cell]:
    """Place, team, a column per level, and a summary column when the table has one."""
    table = {
        CellAddress(row=SHORT_HEADER_ROW, column=SHORT_PLACE_COLUMN): Cell(
            value=SHORT_PLACE_TITLE, style=CellStyle.HEADER
        ),
        CellAddress(row=SHORT_HEADER_ROW, column=SHORT_TEAM_COLUMN): Cell(
            value=SHORT_TEAM_TITLE, style=CellStyle.HEADER
        ),
    }
    for level_number in _short_levels(game):
        table[CellAddress(row=SHORT_HEADER_ROW, column=_short_level_column(level_number))] = Cell(
            value=level_number, style=CellStyle.HEADER
        )
    if total_title is not None:
        table[CellAddress(row=SHORT_HEADER_ROW, column=_short_total_column(game))] = Cell(
            value=total_title, style=CellStyle.HEADER
        )
    return table


def _short_rows(
    table: dict[CellAddress, Cell],
    game: dto.FullGame,
    game_stat: dto.GameStat,
) -> typing.Iterator[tuple[int, TeamPlace]]:
    """Write the place and the name of every team, and hand its row back to be filled."""
    for place_number, place in enumerate(build_standings(game, game_stat), start=1):
        row = SHORT_HEADER_ROW + place_number
        # the place is what the row is called, like the team name next to it
        table[CellAddress(row=row, column=SHORT_PLACE_COLUMN)] = Cell(
            value=place_number, style=CellStyle.HEADER
        )
        table[CellAddress(row=row, column=SHORT_TEAM_COLUMN)] = Cell(
            value=place.team.name, style=CellStyle.TEAM
        )
        yield row, place


def _add_short_averages(
    table: dict[CellAddress, Cell],
    by_level: dict[int, list[timedelta]],
    row: int,
) -> None:
    """A last row of how long a level took on average, under the teams."""
    if not by_level:
        return
    table[CellAddress(row=row, column=SHORT_TEAM_COLUMN)] = Cell(
        value=AVERAGE_TITLE, style=CellStyle.ACCENT
    )
    for level_number, durations in by_level.items():
        average = sum(durations, start=timedelta(seconds=0)) / len(durations)
        table[CellAddress(row=row, column=_short_level_column(level_number))] = Cell(
            value=as_time(average), format=TIME_EXCEL_FORMAT, style=CellStyle.ACCENT
        )


def _short_levels(game: dto.FullGame) -> range:
    """Level numbers of the short table, counted from one."""
    return range(1, len(game.levels) + 1)


def _short_level_column(level_number: int) -> int:
    return SHORT_TEAM_COLUMN + level_number


def _short_total_column(game: dto.FullGame) -> int:
    return _short_level_column(len(game.levels)) + 1
