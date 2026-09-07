from datetime import date, datetime

import pytest

from shvatka.core.season import dto as season_dto
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.tgbot.dialogs.season.calendar import FREE, LINKED, MINE, TAKEN, SlotMark
from shvatka.tgbot.dialogs.season.getters import mark_of, marks_of
from tests.unit.season.conftest import make_player, make_slot

DAY = date(2027, 5, 15)
PUBLISHED_AT = datetime(2026, 8, 1, 10, tzinfo=tz_utc)
GAME = season_dto.LinkedGame(id=7, name="game", start_at=None, number=None)


def test_a_free_date_is_green():
    assert mark_of(make_slot(1, DAY), make_player(1)) == FREE


def test_your_own_date_stands_out_from_someone_elses():
    me = make_player(1)
    assert mark_of(make_slot(1, DAY, owner=me), me) == MINE
    assert mark_of(make_slot(1, DAY, owner=make_player(2)), me) == TAKEN


def test_a_date_with_a_game_says_so_whoever_owns_it():
    me = make_player(1)
    assert mark_of(make_slot(1, DAY, owner=me, game=GAME), me) == LINKED


def test_an_anonymous_reader_sees_every_taken_date_as_taken():
    assert mark_of(make_slot(1, DAY, owner=make_player(2)), None) == TAKEN


def test_marks_are_keyed_by_iso_date():
    me = make_player(1)
    season = season_dto.Season(
        id=1,
        year=2027,
        published_by_id=me.id,
        published_at=PUBLISHED_AT,
        updated_at=PUBLISHED_AT,
        slots=[make_slot(1, DAY), make_slot(2, date(2027, 6, 5), owner=me)],
    )

    assert marks_of(season, me) == {"2027-05-15": FREE, "2027-06-05": MINE}


def test_no_season_means_no_marks():
    assert marks_of(None, make_player(1)) == {}


@pytest.mark.asyncio
async def test_a_day_cell_carries_its_mark():
    data = {"date": DAY, "data": {"slot_marks": {"2027-05-15": FREE}}}

    assert await SlotMark().render_text(data, None) == f"{FREE}15"


@pytest.mark.asyncio
async def test_a_day_with_nothing_planned_is_just_a_number():
    data = {"date": DAY, "data": {"slot_marks": {}}}

    assert await SlotMark().render_text(data, None) == "15"


@pytest.mark.asyncio
async def test_today_keeps_its_brackets():
    data = {"date": DAY, "data": {}}

    assert await SlotMark(today=True).render_text(data, None) == "[15]"
