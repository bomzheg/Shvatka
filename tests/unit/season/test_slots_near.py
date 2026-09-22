from datetime import date, datetime

from shvatka.core.season import dto as season_dto
from shvatka.core.season.rules import find_slots_near
from shvatka.core.utils.datetime_utils import tz_game
from tests.unit.season.conftest import make_player, make_slot

AT = date(2027, 6, 26)


def test_only_dates_within_three_days_are_offered():
    slots = [
        make_slot(1, date(2027, 6, 22)),  # 4 days before
        make_slot(2, date(2027, 6, 23)),  # 3 days before
        make_slot(3, date(2027, 6, 29)),  # 3 days after
        make_slot(4, date(2027, 6, 30)),  # 4 days after
    ]

    found = find_slots_near(slots, AT, make_player(1))

    assert [slot.id for slot in found] == [2, 3]


def test_the_nearest_comes_first():
    slots = [
        make_slot(1, date(2027, 6, 28)),
        make_slot(2, date(2027, 6, 26)),
        make_slot(3, date(2027, 6, 25)),
    ]

    found = find_slots_near(slots, AT, make_player(1))

    assert [slot.id for slot in found] == [2, 3, 1]


def test_a_tie_resolves_to_the_earlier_date():
    slots = [
        make_slot(1, date(2027, 6, 28)),
        make_slot(2, date(2027, 6, 24)),
    ]

    found = find_slots_near(slots, AT, make_player(1))

    assert [slot.id for slot in found] == [2, 1]


def test_someone_elses_date_is_never_offered():
    me = make_player(1)
    slots = [
        make_slot(1, date(2027, 6, 25), owner=make_player(2)),
        make_slot(2, date(2027, 6, 27), owner=me),
        make_slot(3, date(2027, 6, 28)),
    ]

    found = find_slots_near(slots, AT, me)

    assert [slot.id for slot in found] == [2, 3]


def test_a_date_that_already_holds_a_game_is_not_offered():
    me = make_player(1)
    game = season_dto.LinkedGame(
        id=7,
        name="game",
        start_at=datetime(2027, 6, 26, 20, tzinfo=tz_game),
        number=None,
    )
    slots = [make_slot(1, date(2027, 6, 26), owner=me, game=game)]

    assert find_slots_near(slots, AT, me) == []


def test_an_anonymous_caller_sees_only_free_dates():
    slots = [
        make_slot(1, date(2027, 6, 25), owner=make_player(2)),
        make_slot(2, date(2027, 6, 27)),
    ]

    found = find_slots_near(slots, AT, None)

    assert [slot.id for slot in found] == [2]
