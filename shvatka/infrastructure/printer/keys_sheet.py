from io import BytesIO

from matplotlib import font_manager
from matplotlib.backends.backend_pdf import FigureCanvasPdf, PdfPages
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from matplotlib.textpath import TextToPath

from shvatka.core.scenario import dto
from shvatka.core.scenario.adapters import KeysSheetPrinter
from shvatka.infrastructure.printer.keys_layout import (
    LINE_HEIGHT,
    PAGE_HEIGHT_MM,
    PAGE_WIDTH_MM,
    PT_IN_MM,
    SLIP_PADDING_MM,
    KeysSheetLayout,
    Page,
    Sheet,
    Slip,
)

FONT_FAMILIES = (
    "Times New Roman",
    "Liberation Serif",
    "Nimbus Roman",
    "FreeSerif",
    "DejaVu Serif",
)
"""Times New Roman, the font of the game document, or its closest stand-in.

Liberation Serif has the same metrics and is installed in the image; DejaVu
Serif ships with matplotlib itself and closes the list, so there is always
something with Cyrillic in it. Whatever is found is what gets measured, so the
layout holds either way.
"""
KEY_WEIGHT = "normal"
"""The game document doesn't embolden the keys — the size tells them apart."""
CAPTION_COLOR = "0.35"
CUT_LINE_COLOR = "0.8"
CUT_LINE_WIDTH = 0.4
CUT_LINE_STYLE = (0, (2, 2))
MM_IN_INCH = 25.4

_text_to_path = TextToPath()


def font_family() -> str:
    available = set(font_manager.get_font_names())
    return next((family for family in FONT_FAMILIES if family in available), FONT_FAMILIES[-1])


FONT = font_family()


def measure(text: str, font_pt: float) -> float:
    if not text:
        return 0.0
    prop = FontProperties(family=FONT, size=font_pt, weight=KEY_WEIGHT)
    width, _, _ = _text_to_path.get_text_width_height_descent(text, prop, ismath=False)
    return width * PT_IN_MM


class PdfKeysSheetPrinter(KeysSheetPrinter):
    file_extension = "pdf"

    def __init__(self) -> None:
        self.layout = KeysSheetLayout(measure)

    def print_keys_sheet(self, sheet: dto.KeysSheet) -> BytesIO:
        return render(self.layout.plan(sheet))


def render(sheet: Sheet) -> BytesIO:
    result = BytesIO()
    with PdfPages(result) as pdf:
        for page in sheet.pages:
            pdf.savefig(render_page(page))
    result.seek(0)
    return result


def render_page(page: Page) -> Figure:
    figure = Figure(figsize=(PAGE_WIDTH_MM / MM_IN_INCH, PAGE_HEIGHT_MM / MM_IN_INCH))
    FigureCanvasPdf(figure)
    for slip in page.slips:
        render_slip(figure, slip)
    return figure


def render_slip(figure: Figure, slip: Slip) -> None:
    figure.add_artist(
        Rectangle(
            _point(slip.left, slip.top + slip.height),
            slip.width / PAGE_WIDTH_MM,
            slip.height / PAGE_HEIGHT_MM,
            transform=figure.transFigure,
            fill=False,
            edgecolor=CUT_LINE_COLOR,
            linewidth=CUT_LINE_WIDTH,
            linestyle=CUT_LINE_STYLE,
        )
    )
    caption_height = slip.caption_font_pt * LINE_HEIGHT * PT_IN_MM
    line_height = slip.font_pt * LINE_HEIGHT * PT_IN_MM
    # the key and its caption are centred in the slip as one block
    block_height = len(slip.lines) * line_height + caption_height
    first_line_top = slip.top + (slip.height - block_height) / 2
    for i, line in enumerate(slip.lines):
        _text(
            figure,
            slip.left + slip.width / 2,
            first_line_top + (i + 0.5) * line_height,
            line,
            slip.font_pt,
            horizontal="center",
            weight=KEY_WEIGHT,
        )
    caption_middle = first_line_top + len(slip.lines) * line_height + caption_height / 2
    _text(
        figure,
        slip.left + SLIP_PADDING_MM,
        caption_middle,
        slip.caption_name,
        slip.caption_font_pt,
        horizontal="left",
        color=CAPTION_COLOR,
    )
    _text(
        figure,
        slip.left + slip.width - SLIP_PADDING_MM,
        caption_middle,
        slip.caption_date,
        slip.caption_font_pt,
        horizontal="right",
        color=CAPTION_COLOR,
    )


def _text(
    figure: Figure,
    x_mm: float,
    y_mm: float,
    text: str,
    font_pt: float,
    horizontal: str,
    weight: str = "normal",
    color: str = "black",
) -> None:
    x, y = _point(x_mm, y_mm)
    figure.text(
        x,
        y,
        text,
        fontsize=font_pt,
        family=FONT,
        fontweight=weight,
        color=color,
        horizontalalignment=horizontal,
        verticalalignment="center",
    )


def _point(x_mm: float, y_mm: float) -> tuple[float, float]:
    return x_mm / PAGE_WIDTH_MM, 1 - y_mm / PAGE_HEIGHT_MM
