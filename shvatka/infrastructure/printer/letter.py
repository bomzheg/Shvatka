from io import BytesIO
from tempfile import TemporaryFile, NamedTemporaryFile

from pylatex import Document

from shvatka.core.interfaces.printer import Table, TablePrinter


class LatexPrinter(TablePrinter):
    def print_table(self, table: Table) -> BytesIO:
        doc = LatexDocumentBuilder()
        return doc.build()


class LatexDocumentBuilder:
    def __init__(self) -> None:
        self.file = NamedTemporaryFile("wrb")
        self.doc = Document(self.file.name)

    def build(self) -> BytesIO:
        result = BytesIO()
        self.doc.generate_pdf(filepath=self.file.name)
        self.file.seek(0)
        result.write(self.file.read())
        self.file.close()
        return result
