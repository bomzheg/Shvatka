import math
import typing
from dataclasses import dataclass

from shvatka.core.scenario import dto
from shvatka.core.utils.datetime_utils import DATE_FORMAT, tz_game

Measure = typing.Callable[[str, float], float]
"""Width of a text (mm) if it were printed at the given font size (pt)."""

PAGE_WIDTH_MM = 210.0
PAGE_HEIGHT_MM = 297.0
MARGIN_MM = 10.0
"""Printers refuse to draw closer to the edge than this."""
COLUMN_GAP_MM = 4.0
SLIP_PADDING_MM = 2.0
PT_IN_MM = 25.4 / 72

KEY_FONT_MAX_PT = 14.0
"""The size the orgs used in the game document, and it is a good one."""
KEY_FONT_MIN_PT = 12.0
"""Smaller than this is not worth reading in the dark, so the grid grows instead."""
LONG_KEY_FONT_MAX_PT = 24.0
CAPTION_FONT_PT = 10.0
"""Also from the game document — a key is twice the size of what signs it."""
CAPTION_FONT_MIN_PT = 6.0
CAPTION_GAP_MM = 3.0
"""Distance between the name of the game and the date of it inside one caption."""
LINE_HEIGHT = 1.25
MAX_COLUMNS = 4
MAX_COPIES_OF_LONG_KEY = 4
ELLIPSIS = "…"

CONTENT_WIDTH_MM = PAGE_WIDTH_MM - 2 * MARGIN_MM
CONTENT_HEIGHT_MM = PAGE_HEIGHT_MM - 2 * MARGIN_MM


@dataclass(frozen=True)
class Slip:
    lines: tuple[str, ...]
    """The key itself — more than one line only when it doesn't fit on one."""
    font_pt: float
    caption_name: str
    caption_date: str
    caption_font_pt: float
    left: float
    top: float
    width: float
    height: float


@dataclass(frozen=True)
class Page:
    slips: tuple[Slip, ...]


@dataclass(frozen=True)
class Sheet:
    pages: tuple[Page, ...]
    copies: int
    """How many times every ordinary key is printed."""


class KeysSheetLayout:
    def __init__(self, measure: Measure) -> None:
        self.measure = measure

    def plan(self, sheet: dto.KeysSheet) -> Sheet:
        name, date = caption_of(sheet)
        ordinary, long = self.split_by_length(sheet.keys)
        pages, copies = self.grid_pages(ordinary, name, date)
        pages.extend(self.long_key_pages(long, name, date))
        return Sheet(pages=tuple(pages), copies=copies)

    def split_by_length(self, keys: list[str]) -> tuple[list[str], list[str]]:
        widest = CONTENT_WIDTH_MM - 2 * SLIP_PADDING_MM
        ordinary: list[str] = []
        long: list[str] = []
        for key in keys:
            (ordinary if self.measure(key, KEY_FONT_MIN_PT) <= widest else long).append(key)
        return ordinary, long

    def grid_pages(self, keys: list[str], name: str, date: str) -> tuple[list[Page], int]:
        if not keys:
            return [], 0
        columns = self.columns_count(keys, name, date)
        column_width = (CONTENT_WIDTH_MM - (columns - 1) * COLUMN_GAP_MM) / columns
        rows = max(1, int(CONTENT_HEIGHT_MM // self.slip_height()))
        per_page = rows * columns
        copies = max(1, per_page // len(keys))
        slips = [key for key in keys for _ in range(copies)]
        # the rows nobody occupies are given away to the ones that are used
        used_rows = math.ceil(min(len(slips), per_page) / columns)
        row_height = CONTENT_HEIGHT_MM / used_rows
        pages = [
            Page(
                slips=tuple(
                    self.slip(
                        key,
                        left=MARGIN_MM + (i % columns) * (column_width + COLUMN_GAP_MM),
                        top=MARGIN_MM + (i // columns) * row_height,
                        width=column_width,
                        height=row_height,
                        name=name,
                        date=date,
                    )
                    for i, key in enumerate(slips[start : start + per_page])
                )
            )
            for start in range(0, len(slips), per_page)
        ]
        return pages, copies

    def columns_count(self, keys: list[str], name: str, date: str) -> int:
        longest = max(self.measure(key, KEY_FONT_MIN_PT) for key in keys)
        caption = self.caption_width(name, date, CAPTION_FONT_MIN_PT)
        for columns in range(MAX_COLUMNS, 1, -1):
            width = (CONTENT_WIDTH_MM - (columns - 1) * COLUMN_GAP_MM) / columns
            if max(longest, caption) <= width - 2 * SLIP_PADDING_MM:
                return columns
        return 1

    def slip_height(self) -> float:
        return (KEY_FONT_MAX_PT + CAPTION_FONT_PT) * LINE_HEIGHT * PT_IN_MM + 2 * SLIP_PADDING_MM

    def slip(
        self,
        key: str,
        left: float,
        top: float,
        width: float,
        height: float,
        name: str,
        date: str,
    ) -> Slip:
        available = width - 2 * SLIP_PADDING_MM
        caption_font, caption_name = self.caption(name, date, available)
        return self.fitted(
            lines=(key,),
            font_pt=self.fitting_font(key, available, KEY_FONT_MAX_PT),
            caption_name=caption_name,
            caption_date=date,
            caption_font_pt=caption_font,
            left=left,
            top=top,
            width=width,
            height=height,
        )

    def fitted(
        self,
        lines: tuple[str, ...],
        font_pt: float,
        caption_name: str,
        caption_date: str,
        caption_font_pt: float,
        left: float,
        top: float,
        width: float,
        height: float,
    ) -> Slip:
        content = max(
            *(self.measure(line, font_pt) for line in lines),
            self.caption_width(caption_name, caption_date, caption_font_pt),
        )
        fit_width = min(width, content + 2 * SLIP_PADDING_MM)
        fit_height = min(height, self.block_height(len(lines), font_pt, caption_font_pt))
        return Slip(
            lines=lines,
            font_pt=font_pt,
            caption_name=caption_name,
            caption_date=caption_date,
            caption_font_pt=caption_font_pt,
            left=left + (width - fit_width) / 2,
            top=top + (height - fit_height) / 2,
            width=fit_width,
            height=fit_height,
        )

    def long_key_pages(self, keys: list[str], name: str, date: str) -> list[Page]:
        return [self.long_key_page(key, name, date) for key in keys]

    def long_key_page(self, key: str, name: str, date: str) -> Page:
        available = CONTENT_WIDTH_MM - 2 * SLIP_PADDING_MM
        caption_font, caption_name = self.caption(name, date, available)
        font = LONG_KEY_FONT_MAX_PT
        while font > KEY_FONT_MIN_PT:
            lines = self.wrap(key, font, available)
            if self.block_height(len(lines), font, caption_font) <= CONTENT_HEIGHT_MM:
                break
            font -= 1
        lines = self.wrap(key, font, available)
        height = self.block_height(len(lines), font, caption_font)
        copies = min(MAX_COPIES_OF_LONG_KEY, max(1, int(CONTENT_HEIGHT_MM // height)))
        row_height = CONTENT_HEIGHT_MM / copies
        return Page(
            slips=tuple(
                self.fitted(
                    lines=lines,
                    font_pt=font,
                    caption_name=caption_name,
                    caption_date=date,
                    caption_font_pt=caption_font,
                    left=MARGIN_MM,
                    top=MARGIN_MM + i * row_height,
                    width=CONTENT_WIDTH_MM,
                    height=row_height,
                )
                for i in range(copies)
            )
        )

    def block_height(self, lines: int, font_pt: float, caption_font_pt: float) -> float:
        return (lines * font_pt + caption_font_pt) * LINE_HEIGHT * PT_IN_MM + 2 * SLIP_PADDING_MM

    def wrap(self, key: str, font_pt: float, available: float) -> tuple[str, ...]:
        lines: list[str] = []
        current = ""
        for char in key:
            if current and self.measure(current + char, font_pt) > available:
                lines.append(current)
                current = ""
            current += char
        if current:
            lines.append(current)
        return tuple(lines)

    def caption(self, name: str, date: str, available: float) -> tuple[float, str]:
        font = CAPTION_FONT_PT
        # only the text scales with the font size, the gap between name and date doesn't
        needed = self.measure(name, font) + self.measure(date, font)
        room = available - CAPTION_GAP_MM
        if needed > room:
            font = max(CAPTION_FONT_MIN_PT, font * room / needed)
        while name and self.caption_width(name, date, font) > available:
            name = name[: -2 if name.endswith(ELLIPSIS) else -1] + ELLIPSIS
        return font, name

    def caption_width(self, name: str, date: str, font_pt: float) -> float:
        return self.measure(name, font_pt) + self.measure(date, font_pt) + CAPTION_GAP_MM

    def fitting_font(self, text: str, available: float, maximum: float) -> float:
        width = self.measure(text, KEY_FONT_MIN_PT)
        if width <= 0:
            return maximum
        return min(maximum, KEY_FONT_MIN_PT * available / width)


def caption_of(sheet: dto.KeysSheet) -> tuple[str, str]:
    date = sheet.game_date.astimezone(tz=tz_game).strftime(DATE_FORMAT) if sheet.game_date else ""
    return f"Игра: {sheet.game_name}", date
