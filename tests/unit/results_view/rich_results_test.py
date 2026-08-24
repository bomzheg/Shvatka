from datetime import datetime, time
from unittest import mock

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendMessage
from aiogram.types import (
    InputRichBlockParagraph,
    InputRichBlockPhoto,
    InputRichBlockSectionHeading,
    InputRichBlockTable,
    RichTextUnderline,
)

from shvatka.common.data_examples import game_example
from shvatka.core.games.results import LEVEL_DURATIONS_TITLE, LEVEL_TIMES_TITLE
from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.core.interfaces.printer import (
    DATETIME_EXCEL_FORMAT,
    TIME_EXCEL_FORMAT,
    Cell,
    CellAddress,
    CellStyle,
    Table,
)
from shvatka.infrastructure.picture import ResultsPainter
from shvatka.tgbot.views.results.rich import (
    TOO_WIDE,
    ResultsRichSender,
    build_results_message,
    render_table,
)


def _table(fields: dict[tuple[int, int], Cell], hidden: list[int] | None = None) -> Table:
    return Table(
        fields={
            CellAddress(row=row, column=column): cell for (row, column), cell in fields.items()
        },
        hidden_columns=hidden or [],
    )


def test_rendered_table_is_a_rectangle() -> None:
    table = _table(
        {
            (1, 1): Cell(value="Команда", style=CellStyle.HEADER),
            (1, 2): Cell(value=1, style=CellStyle.HEADER),
            (2, 1): Cell(value="Gryffindor", style=CellStyle.TEAM),
            # the team never took the level, so nothing was written to (2, 2)
        }
    )

    block = render_table(table)

    assert isinstance(block, InputRichBlockTable)
    assert [[cell.text for cell in row] for row in block.cells] == [
        ["Команда", "1"],
        ["Gryffindor", None],
    ]


def test_header_cells_are_marked_and_values_are_not() -> None:
    table = _table(
        {
            (1, 1): Cell(value="Команда", style=CellStyle.HEADER),
            (1, 2): Cell(value=1, style=CellStyle.HEADER),
            (2, 1): Cell(value="Gryffindor", style=CellStyle.TEAM),
            (2, 2): Cell(value=datetime(2023, 3, 19, 2, 30, tzinfo=tz_game), style=CellStyle.DATA),
        }
    )

    block = render_table(table)

    assert [[cell.is_header for cell in row] for row in block.cells] == [
        [True, True],
        [True, False],
    ]
    assert [[cell.align for cell in row] for row in block.cells] == [
        ["center", "center"],
        ["left", "center"],
    ]


def test_the_best_value_of_a_column_is_underlined() -> None:
    """Bold is what telegram draws a header cell with, so a bold value reads as a header."""
    table = _table({(1, 1): Cell(value=1, style=CellStyle.BEST)})

    ((cell,),) = render_table(table).cells

    assert cell.text == RichTextUnderline(text="1")


def test_time_is_rendered_the_way_the_cell_asks() -> None:
    table = _table(
        {
            (1, 1): Cell(
                value=datetime(2023, 3, 19, 2, 30, 15, tzinfo=tz_game), format=TIME_EXCEL_FORMAT
            ),
            (1, 2): Cell(value=time(2, 30, 15), format=DATETIME_EXCEL_FORMAT),
        }
    )

    ((short, full),) = render_table(table).cells

    assert (short.text, full.text) == ("02:30", "02:30:15")


def test_hidden_columns_are_not_rendered() -> None:
    table = _table(
        {
            (1, 1): Cell(value="Команда"),
            (1, 2): Cell(value="служебная"),
            (1, 3): Cell(value=1),
        },
        hidden=[2],
    )

    ((first, second),) = render_table(table).cells

    assert (first.text, second.text) == ("Команда", "1")


def test_results_message_shows_the_table_under_the_picture() -> None:
    table = _table({(1, 1): Cell(value="Команда", style=CellStyle.HEADER)})

    message = build_results_message(game_example, table, photo_file_id="results-file-id")

    assert message.blocks is not None
    heading, photo, rendered, footer = message.blocks
    assert isinstance(heading, InputRichBlockSectionHeading)
    assert heading.text == "Результаты игры №20 «Funny game»"
    assert isinstance(photo, InputRichBlockPhoto)
    assert photo.photo.media == "results-file-id"
    assert isinstance(rendered, InputRichBlockTable)
    assert isinstance(footer, InputRichBlockParagraph)
    assert footer.text == "Игра началась 19.03.23 02:00"


def test_results_message_captions_both_tables() -> None:
    takes = _table({(1, 1): Cell(value="Команда", style=CellStyle.HEADER)})
    durations = _table({(1, 1): Cell(value="Команда", style=CellStyle.HEADER)})

    message = build_results_message(game_example, takes, durations)

    assert message.blocks is not None
    assert [
        block.caption for block in message.blocks if isinstance(block, InputRichBlockTable)
    ] == [LEVEL_TIMES_TITLE, LEVEL_DURATIONS_TITLE]


def test_results_message_without_a_picture() -> None:
    table = _table({(1, 1): Cell(value="Команда", style=CellStyle.HEADER)})

    message = build_results_message(game_example, table)

    assert message.blocks is not None
    assert not any(isinstance(block, InputRichBlockPhoto) for block in message.blocks)


@pytest.mark.asyncio
async def test_a_table_too_wide_falls_back_to_the_picture() -> None:
    """A game with more levels than a table may have columns still shows its chart."""
    bot = _bot()
    bot.send_rich_message = mock.AsyncMock(  # type: ignore[method-assign]
        side_effect=TelegramBadRequest(
            method=SendMessage(chat_id=1, text="x"),
            message=f"Bad Request: {TOO_WIDE}",
        )
    )
    bot.send_photo = mock.AsyncMock()  # type: ignore[method-assign]
    sender = ResultsRichSender(bot, _painter())

    await sender.send_results(chat_id=1, game=game_example, game_stat=dto.GameStat(level_times={}))

    bot.send_photo.assert_awaited_once()
    assert bot.send_photo.await_args.kwargs["photo"] == "results-file-id"


@pytest.mark.asyncio
async def test_the_picture_is_not_sent_twice_when_the_message_fits() -> None:
    bot = _bot()
    bot.send_rich_message = mock.AsyncMock()  # type: ignore[method-assign]
    bot.send_photo = mock.AsyncMock()  # type: ignore[method-assign]
    sender = ResultsRichSender(bot, _painter())

    await sender.send_results(chat_id=1, game=game_example, game_stat=dto.GameStat(level_times={}))

    bot.send_photo.assert_not_awaited()


def _bot() -> Bot:
    return Bot(token="42:TESTTESTTESTTESTTESTTESTTESTTESTTES", session=mock.AsyncMock(BaseSession))


def _painter() -> ResultsPainter:
    painter = mock.AsyncMock(ResultsPainter)
    painter.paint_game_results.return_value = "results-file-id"
    return painter
