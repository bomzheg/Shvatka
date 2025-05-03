import typing
from io import BytesIO

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from shvatka.core.interfaces.printer import Table, TablePrinter


class ExcellPrinter(TablePrinter):
    def print_table(self, table: Table) -> BytesIO:
        result = BytesIO()
        print_table(table, result)
        result.seek(0)
        return result


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
    for col in worksheet.columns:  # type: typing.Any  # =(
        new_len = max([2, *[len(str(cell.value or "")) for cell in col]])
        worksheet.column_dimensions[col[0].column_letter].width = new_len
