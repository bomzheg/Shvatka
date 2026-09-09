from datetime import date, datetime, timedelta
from typing import Any

from shvatka.core.season import dto as season_dto
from shvatka.core.season.rules import collapse_changes
from shvatka.core.utils.datetime_utils import tz_utc

BASE = datetime(2027, 6, 1, 9, tzinfo=tz_utc)


def change(
    id_: int,
    type_: season_dto.ChangeType,
    payload: dict[str, Any],
    *,
    slot_id: int | None = 1,
) -> season_dto.ScheduleChange:
    return season_dto.ScheduleChange(
        id=id_,
        season_id=1,
        type=type_,
        created_at=BASE + timedelta(minutes=id_),
        slot_id=slot_id,
        payload=payload,
    )


def moved(id_: int, from_: date, to: date, *, slot_id: int | None = 1):
    return change(
        id_,
        season_dto.ChangeType.slot_moved,
        {"from": from_.isoformat(), "to": to.isoformat(), "date": to.isoformat()},
        slot_id=slot_id,
    )


def test_repeated_moves_of_one_date_become_one_line():
    digests = collapse_changes(
        [
            moved(1, date(2027, 6, 26), date(2027, 6, 27)),
            moved(2, date(2027, 6, 27), date(2027, 6, 28)),
            moved(3, date(2027, 6, 28), date(2027, 7, 3)),
        ]
    )

    assert len(digests) == 1
    assert digests[0].moved
    assert digests[0].date_before == date(2027, 6, 26)
    assert digests[0].date_after == date(2027, 7, 3)
    assert digests[0].day == date(2027, 7, 3)


def test_a_date_moved_and_moved_back_drops_out():
    digests = collapse_changes(
        [
            moved(1, date(2027, 6, 26), date(2027, 6, 27)),
            moved(2, date(2027, 6, 27), date(2027, 6, 26)),
        ]
    )

    assert digests == []


def test_take_then_release_becomes_nothing():
    day = date(2027, 6, 26).isoformat()
    digests = collapse_changes(
        [
            change(1, season_dto.ChangeType.slot_taken, {"date": day, "author": "harry"}),
            change(2, season_dto.ChangeType.slot_released, {"date": day, "author": "harry"}),
        ]
    )

    assert digests == []


def test_release_then_take_reports_the_new_owner():
    day = date(2027, 6, 26).isoformat()
    digests = collapse_changes(
        [
            change(1, season_dto.ChangeType.slot_released, {"date": day, "author": "harry"}),
            change(2, season_dto.ChangeType.slot_taken, {"date": day, "author": "hermione"}),
        ]
    )

    assert len(digests) == 1
    assert digests[0].owner == "hermione"
    assert digests[0].released is False


def test_the_last_taker_of_the_day_wins():
    day = date(2027, 6, 26).isoformat()
    digests = collapse_changes(
        [
            change(1, season_dto.ChangeType.slot_taken, {"date": day, "author": "harry"}),
            change(2, season_dto.ChangeType.slot_taken, {"date": day, "author": "gryffindor"}),
        ]
    )

    assert [digest.owner for digest in digests] == ["gryffindor"]


def test_a_date_added_and_removed_the_same_day_never_happened():
    day = date(2027, 8, 1).isoformat()
    digests = collapse_changes(
        [
            change(1, season_dto.ChangeType.slot_added, {"date": day}, slot_id=None),
            change(
                2,
                season_dto.ChangeType.slot_taken,
                {"date": day, "author": "harry"},
                slot_id=None,
            ),
            change(3, season_dto.ChangeType.slot_removed, {"date": day}, slot_id=None),
        ]
    )

    assert digests == []


def test_a_removed_date_is_reported_once():
    day = date(2027, 8, 1).isoformat()
    digests = collapse_changes(
        [change(1, season_dto.ChangeType.slot_removed, {"date": day}, slot_id=None)]
    )

    assert len(digests) == 1
    assert digests[0].removed is True
    assert digests[0].day == date(2027, 8, 1)


def test_linking_and_unlinking_a_game_cancels_out():
    day = date(2027, 6, 26).isoformat()
    digests = collapse_changes(
        [
            change(
                1,
                season_dto.ChangeType.slot_game_linked,
                {"date": day, "game": "my game", "game_id": 7},
            ),
            change(
                2,
                season_dto.ChangeType.slot_game_unlinked,
                {"date": day, "game": "my game", "game_id": 7},
            ),
        ]
    )

    assert digests == []


def test_each_date_gets_its_own_line_ordered_by_date():
    digests = collapse_changes(
        [
            change(
                1,
                season_dto.ChangeType.slot_note_changed,
                {"date": date(2027, 7, 17).isoformat(), "note": "зимняя игра"},
                slot_id=2,
            ),
            moved(2, date(2027, 6, 26), date(2027, 6, 27), slot_id=1),
        ]
    )

    assert [digest.day for digest in digests] == [date(2027, 6, 27), date(2027, 7, 17)]
