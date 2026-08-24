import enum
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from io import BytesIO
from typing import Protocol

DATETIME_EXCEL_FORMAT = "HH:MM:SS"


class CellStyle(enum.Enum):
    """How a cell should look. The printer decides what that means in a real file."""

    PLAIN = enum.auto()
    TITLE = enum.auto()
    """Name of the whole document."""
    SECTION = enum.auto()
    """Caption of one block of the document."""
    HEADER = enum.auto()
    """Column header inside a block."""
    TEAM = enum.auto()
    """Row header — the team a row belongs to."""
    DATA = enum.auto()
    """An ordinary value inside a block."""
    ACCENT = enum.auto()
    """A summary value — an average or a total."""
    BEST = enum.auto()
    """The best value of its column."""


@dataclass(kw_only=True, frozen=True)
class CellAddress:
    column: int
    row: int

    def shift(self, rows: int = 0, columns: int = 0) -> "CellAddress":
        return CellAddress(column=self.column + columns, row=self.row + rows)

    def to_dict(self) -> dict[str, int]:
        return {"row": self.row, "column": self.column}


@dataclass(kw_only=True)
class Cell:
    value: str | datetime | int | float | time | None
    """None keeps the cell empty — it is still drawn, and a chart reads it as a gap."""
    format: str | None = None
    style: CellStyle = CellStyle.PLAIN


@dataclass(kw_only=True, frozen=True)
class CellRange:
    start: CellAddress
    end: CellAddress


class SeriesKind(enum.Enum):
    BAR = enum.auto()
    LINE = enum.auto()


@dataclass(kw_only=True)
class ChartSeries:
    title: CellAddress
    """Cell holding the name of the series."""
    value_range: CellRange
    kind: SeriesKind = SeriesKind.BAR
    accent: bool = False
    """A reference series (an average, say) rather than one more entity."""


@dataclass(kw_only=True)
class Chart:
    title: str
    anchor: CellAddress
    """Top left cell the chart is pinned to."""
    categories: CellRange
    series: list[ChartSeries]
    x_title: str | None = None
    y_title: str | None = None
    y_format: str | None = None
    width: int = 30
    """Centimetres."""
    height: int = 12
    """Centimetres."""


@dataclass(kw_only=True, frozen=True)
class TableBlock:
    """One block of a table: what it is called, and the rows it occupies.

    A file shows every block of a table at once, one under another. Anything
    that cannot (a chat message, a web page) needs to know where one block ends
    and the next begins, and what to call each — that is all this says.
    """

    caption: str
    first_row: int
    """Row of the block's own header, the one carrying its caption."""
    last_row: int


@dataclass(kw_only=True)
class Table:
    fields: dict[CellAddress, Cell]
    blocks: list[TableBlock] = field(default_factory=list)
    """The blocks the table is made of, in the order they are laid out."""
    charts: list[Chart] = field(default_factory=list)
    freeze: CellAddress | None = None
    """Cell above and left of which everything stays put while scrolling."""
    hidden_columns: list[int] = field(default_factory=list)
    """Columns kept out of the way — present, but not shown until asked for."""


def as_time(td: timedelta) -> time:
    hours = td.seconds // 3600
    minutes = (td.seconds - hours * 3600) // 60
    seconds = td.seconds - hours * 3600 - minutes * 60
    return time(hours, minutes, seconds, td.microseconds)


class TablePrinter(Protocol):
    def print_table(self, table: Table) -> BytesIO:
        raise NotImplementedError
