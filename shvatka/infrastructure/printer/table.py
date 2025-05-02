import typing
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

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
