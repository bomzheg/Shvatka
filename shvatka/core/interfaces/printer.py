from dataclasses import dataclass
from datetime import datetime, time, timedelta
from io import BytesIO
from typing import Protocol

DATETIME_EXCEL_FORMAT = "HH:MM:SS"


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
    value: str | datetime | int | time
    format: str | None = None


@dataclass(kw_only=True)
class Table:
    fields: dict[CellAddress, Cell]


def as_time(td: timedelta) -> time:
    hours = td.seconds // 3600
    minutes = (td.seconds - hours * 3600) // 60
    seconds = td.seconds - hours * 3600 - minutes * 60
    return time(hours, minutes, seconds, td.microseconds)


class TablePrinter(Protocol):
    def print_table(self, table: Table) -> BytesIO:
        raise NotImplementedError
