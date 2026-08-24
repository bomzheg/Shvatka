from datetime import datetime, time

from aiogram.types import (
    InputRichBlockParagraph,
    InputRichBlockPhoto,
    InputRichBlockSectionHeading,
    InputRichBlockTable,
    RichTextBold,
)

from shvatka.common.data_examples import game_example
from shvatka.core.games.results import LEVEL_DURATIONS_TITLE, LEVEL_TIMES_TITLE
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.core.interfaces.printer import (
    DATETIME_EXCEL_FORMAT,
    TIME_EXCEL_FORMAT,
    Cell,
    CellAddress,
    CellStyle,
    Table,
)
from shvatka.tgbot.views.results.rich import build_results_message, render_table


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


def test_the_best_value_of_a_column_is_bold() -> None:
    table = _table({(1, 1): Cell(value=1, style=CellStyle.BEST)})

    ((cell,),) = render_table(table).cells

    assert cell.text == RichTextBold(text="1")


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
