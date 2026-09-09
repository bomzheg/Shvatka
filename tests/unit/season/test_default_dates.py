from datetime import date
from itertools import pairwise

import pytest

from shvatka.core.season.rules import (
    SEASON_SLOT_INTERVAL,
    SEASON_SLOTS_COUNT,
    default_slot_dates,
    first_saturday_after,
)

SATURDAY = 5


@pytest.mark.parametrize(
    ("year", "expected"),
    [
        # 9 May 2026 is itself a Saturday, and "strictly after" skips it
        (2026, date(2026, 5, 16)),
        (2027, date(2027, 5, 15)),
        (2028, date(2028, 5, 13)),
    ],
)
def test_first_date_is_the_saturday_strictly_after_9_may(year: int, expected: date):
    assert default_slot_dates(year)[0] == expected


@pytest.mark.parametrize("year", [2026, 2027, 2028, 2029, 2030])
def test_nine_saturdays_every_three_weeks(year: int):
    dates = default_slot_dates(year)

    assert len(dates) == SEASON_SLOTS_COUNT
    assert all(day.weekday() == SATURDAY for day in dates)
    assert all(later - earlier == SEASON_SLOT_INTERVAL for earlier, later in pairwise(dates))


@pytest.mark.parametrize("year", [2026, 2027, 2028, 2029, 2030])
def test_the_last_date_lands_in_the_second_half_of_october(year: int):
    last = default_slot_dates(year)[-1]

    assert last.month == 10
    assert last.day >= 15


@pytest.mark.parametrize("year", [2026, 2027, 2028])
def test_every_date_is_inside_the_season_year(year: int):
    assert all(day.year == year for day in default_slot_dates(year))


def test_a_saturday_is_pushed_a_whole_week():
    saturday = date(2026, 5, 9)
    assert saturday.weekday() == SATURDAY

    assert first_saturday_after(saturday) == date(2026, 5, 16)


def test_the_day_before_a_saturday_moves_by_one():
    assert first_saturday_after(date(2026, 5, 8)) == date(2026, 5, 9)
