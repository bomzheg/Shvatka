"""Results as a telegram rich message: the chart with the standings table under it.

A rich message (Bot API 10.1) carries structured blocks rather than one string,
so the table the game exports to a file is shown right in the chat — the file
stays available, but nobody has to open it to see who won.
"""

import logging
from datetime import datetime, time

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    InputMediaPhoto,
    InputRichBlockParagraph,
    InputRichBlockPhoto,
    InputRichBlockSectionHeading,
    InputRichBlockTable,
    InputRichBlockUnion,
    InputRichMessage,
    Message,
    RichBlockTableCell,
    RichTextUnderline,
    RichTextUnion,
)
from aiogram.utils.text_decorations import html_decoration as hd

from shvatka.core.games.results import (
    LEVEL_DURATIONS_TITLE,
    LEVEL_TIMES_TITLE,
    build_short_durations_table,
    build_short_results_table,
)
from shvatka.core.interfaces.printer import Cell, CellAddress, CellStyle, Table
from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import TIME_FORMAT
from shvatka.infrastructure.picture import ResultsPainter
from shvatka.tgbot.views.jinja_filters.timezone import datetime_filter

logger = logging.getLogger(__name__)

HEADING_SIZE = 3
"""Relative font size of the message heading; 1 is the largest, 6 the smallest."""

LEFT_STYLES = frozenset({CellStyle.PLAIN, CellStyle.TITLE, CellStyle.SECTION, CellStyle.TEAM})
"""Styles of the cells a row is read by — kept against the left edge."""
HEADER_STYLES = frozenset({CellStyle.HEADER, CellStyle.TEAM})
"""Styles telegram draws as a header cell rather than as a value."""
MARKED_STYLES = frozenset({CellStyle.BEST, CellStyle.ACCENT, CellStyle.TITLE})
"""Styles telegram underlines. Bold is what it draws a header cell with, so a
bold value reads as one more header rather than as the best of its column."""

TOO_WIDE = "RICH_MESSAGE_TABLE_COLS_TOO_MANY"
"""What telegram answers when a game has more levels than a table may have columns."""

FALLBACK_CAPTION = "Таблица не поместилась в сообщение — она в xlsx-файле."

EXCEL_TIME_DIRECTIVES = {"HH": "%H", "MM": "%M", "SS": "%S"}
"""How the excel number format of a cell reads as a ``strftime`` one."""


def render_table(table: Table, caption: str | None = None) -> InputRichBlockTable:
    """Draw a table of cells addressed by row and column as a telegram table block.

    Everything the address grid has no cell for is drawn as an empty cell, so the
    rows stay aligned whatever the table left out.
    """
    rows = max((address.row for address in table.fields), default=0)
    columns = max((address.column for address in table.fields), default=0)
    hidden = set(table.hidden_columns)
    return InputRichBlockTable(
        cells=[
            [
                _render_cell(table.fields.get(CellAddress(row=row, column=column)))
                for column in range(1, columns + 1)
                if column not in hidden
            ]
            for row in range(1, rows + 1)
        ],
        is_bordered=True,
        is_striped=True,
        caption=caption,
    )


def results_title(game: dto.Game) -> str:
    return f"Результаты игры №{game.number} «{game.name}»"


def build_results_message(
    game: dto.Game,
    takes: Table,
    durations: Table | None = None,
    photo_file_id: str | None = None,
) -> InputRichMessage:
    """The whole results post: what game it is, the chart of it, and the tables under it.

    Both tables are the same grid of teams by levels — the first says when a
    level was taken, the second how long it took — so their captions are what
    tells them apart.
    """
    blocks: list[InputRichBlockUnion] = [
        InputRichBlockSectionHeading(text=results_title(game), size=HEADING_SIZE)
    ]
    if photo_file_id is not None:
        blocks.append(InputRichBlockPhoto(photo=InputMediaPhoto(media=photo_file_id)))
    blocks.append(render_table(takes, caption=LEVEL_TIMES_TITLE))
    if durations is not None:
        blocks.append(render_table(durations, caption=LEVEL_DURATIONS_TITLE))
    if game.start_at is not None:
        blocks.append(
            InputRichBlockParagraph(text=f"Игра началась {datetime_filter(game.start_at)}")
        )
    # team names are ordinary text: a hashtag or an @ in one is a name, not a link
    return InputRichMessage(blocks=blocks, skip_entity_detection=True)


class ResultsRichSender:
    """Sends the results of a game as a rich message, painting the chart if needed."""

    def __init__(self, bot: Bot, results_painter: ResultsPainter) -> None:
        self.bot = bot
        self.results_painter = results_painter

    async def send_results(
        self,
        chat_id: int,
        game: dto.FullGame,
        game_stat: dto.GameStat,
    ) -> Message:
        photo_file_id = await self.results_painter.paint_game_results(game, game_stat)
        try:
            return await self.bot.send_rich_message(
                chat_id=chat_id,
                rich_message=build_results_message(
                    game=game,
                    takes=build_short_results_table(game, game_stat),
                    durations=build_short_durations_table(game, game_stat),
                    photo_file_id=photo_file_id,
                ),
            )
        except TelegramBadRequest as e:
            # a game long enough has more levels than a table may have columns,
            # and nothing narrower is worth trying — both tables are that wide
            if TOO_WIDE in (e.message or ""):
                logger.info(
                    "game %s has more levels than a table may have columns, "
                    "sending the picture alone",
                    game.id,
                )
            else:
                logger.warning(
                    "results of game %s rejected as a rich message, sending the picture alone",
                    game.id,
                    exc_info=e,
                )
            return await self.send_picture(chat_id, game, photo_file_id)

    async def send_picture(self, chat_id: int, game: dto.Game, photo_file_id: str) -> Message:
        """The results as they were shown before the tables: the chart and nothing else."""
        return await self.bot.send_photo(
            chat_id=chat_id,
            photo=photo_file_id,
            caption=f"{hd.bold(hd.quote(results_title(game)))}\n{FALLBACK_CAPTION}",
        )


def _render_cell(cell: Cell | None) -> RichBlockTableCell:
    if cell is None:
        return RichBlockTableCell(align="center", valign="middle")
    return RichBlockTableCell(
        align="left" if cell.style in LEFT_STYLES else "center",
        valign="middle",
        text=_render_value(cell),
        is_header=cell.style in HEADER_STYLES,
    )


def _render_value(cell: Cell) -> RichTextUnion | None:
    if cell.value is None:
        return None
    if isinstance(cell.value, (datetime, time)):
        text = cell.value.strftime(_time_format(cell.format))
    else:
        text = str(cell.value)
    return RichTextUnderline(text=text) if cell.style in MARKED_STYLES else text


def _time_format(excel_format: str | None) -> str:
    """Translate the excel number format of a cell into a ``strftime`` one."""
    if excel_format is None:
        return TIME_FORMAT
    result = excel_format
    for token, directive in EXCEL_TIME_DIRECTIVES.items():
        result = result.replace(token, directive)
    return result
