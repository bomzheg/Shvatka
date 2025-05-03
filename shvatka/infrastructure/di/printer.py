from dishka import Provider, Scope, provide

from shvatka.core.interfaces.printer import TablePrinter
from shvatka.infrastructure.printer.table import ExcellPrinter


class PrinterProvider(Provider):
    scope = Scope.APP

    excel_printer = provide(ExcellPrinter, provides=TablePrinter)
