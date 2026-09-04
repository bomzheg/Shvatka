import dataclasses
from datetime import timedelta
from uuid import uuid4

import pytest

from shvatka.common.data_examples import GAME_START_EXAMPLE, game_example
from shvatka.core.games.dto import BonusEvent, BonusSource
from shvatka.core.games.results import (
    BONUSES_TITLE,
    CHRONOLOGY_TITLE,
    LABEL_COLUMN,
    LEVEL_DURATIONS_TITLE,
    LEVEL_TIMES_TITLE,
    build_results_table,
)
from shvatka.core.interfaces.printer import CellAddress, CellStyle, Table, TableBlock
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import action
from shvatka.core.utils.exceptions import GameNotFinished

WINNER = dto.Team(id=1, name="Gryffindor", captain=None, is_dummy=False, description=None)
SECOND = dto.Team(id=2, name="Slytherin", captain=None, is_dummy=False, description=None)
LOSER = dto.Team(id=3, name="Hufflepuff", captain=None, is_dummy=False, description=None)


@pytest.fixture
def game_stat() -> dto.GameStat:
    return dto.GameStat(
        level_times={
            LOSER: _level_times(LOSER, {0: 0, 1: 40, 2: 80}),
            SECOND: _level_times(SECOND, {0: 0, 1: 20, 2: 70, 3: 100, 4: 130}),
            WINNER: _level_times(WINNER, {0: 0, 1: 30, 2: 60, 3: 90, 4: 120}),
        }
    )


def _level_times(team: dto.Team, offsets: dict[int, int]) -> list[dto.LevelTime]:
    return [
        dto.LevelTime(
            id=team.id * 100 + level_number,
            game=game_example,
            team=team,
            level_number=level_number,
            start_at=GAME_START_EXAMPLE + timedelta(minutes=offset),
        )
        for level_number, offset in offsets.items()
    ]


def test_teams_are_ordered_by_result(game_stat: dto.GameStat) -> None:
    table = build_results_table(game_example, game_stat)
    times = next(block for block in table.blocks if block.caption == LEVEL_TIMES_TITLE)

    assert _teams_of(table, times) == ["Gryffindor", "Slytherin", "Hufflepuff"]


def test_every_block_of_the_table_is_reported(game_stat: dto.GameStat) -> None:
    table = build_results_table(game_example, game_stat)

    assert [block.caption for block in table.blocks] == [
        LEVEL_TIMES_TITLE,
        LEVEL_DURATIONS_TITLE,
        CHRONOLOGY_TITLE,
    ]


def test_blocks_do_not_overlap(game_stat: dto.GameStat) -> None:
    table = build_results_table(game_example, game_stat)

    for previous, block in zip(table.blocks[:-1], table.blocks[1:], strict=False):
        assert previous.last_row < block.first_row


def test_a_block_covers_its_own_rows(game_stat: dto.GameStat) -> None:
    table = build_results_table(game_example, game_stat)
    times = next(block for block in table.blocks if block.caption == LEVEL_TIMES_TITLE)

    caption = table.fields[CellAddress(row=times.first_row, column=LABEL_COLUMN)]
    assert caption.value == LEVEL_TIMES_TITLE
    assert caption.style is CellStyle.SECTION
    assert _teams_of(table, times) == ["Gryffindor", "Slytherin", "Hufflepuff"]


def test_bonuses_become_a_block_of_their_own(game_stat: dto.GameStat) -> None:
    bonus = BonusEvent(
        at=GAME_START_EXAMPLE + timedelta(minutes=35),
        effects=action.Effects(id=uuid4(), bonus_minutes=5),
        source=BonusSource.key,
        key="SHБОНУС",
        level_time_id=WINNER.id * 100 + 1,
    )

    table = build_results_table(game_example, game_stat, bonuses={WINNER.id: [bonus]})

    assert BONUSES_TITLE in [block.caption for block in table.blocks]


def test_of_unfinished_game(game_stat: dto.GameStat) -> None:
    started = dataclasses.replace(game_example, status=enums.GameStatus.started)

    with pytest.raises(GameNotFinished):
        build_results_table(started, game_stat)


def _teams_of(table: Table, block: TableBlock) -> list[str]:
    return [
        str(cell.value)
        for row in range(block.first_row, block.last_row + 1)
        if (cell := table.fields.get(CellAddress(row=row, column=LABEL_COLUMN)))
        and cell.style is CellStyle.TEAM
    ]
