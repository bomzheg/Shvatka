"""What a day of the schedule looks like in telegram.

The marks are the whole of the calendar's language — a day cell has room for
one character and a number — so what they mean is worth pinning down.
"""

import typing
from datetime import date, datetime

import pytest
from aiogram_dialog.api.protocols import DialogManager

from shvatka.core.models import dto
from shvatka.core.season import dto as season_dto
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.core.views.game import GameLogEvent, GameLogType
from shvatka.tgbot.dialogs.season.calendar import MARKS_KEY, SlotDayText
from shvatka.tgbot.views.game import render_game_log
from shvatka.tgbot.views.season import FREE, LINKED, MINE, TAKEN, slot_mark

DAY = date(2026, 5, 16)


def make_player(id_: int) -> dto.Player:
    return dto.Player(id=id_, can_be_author=True, is_dummy=False, username=f"player{id_}")


def make_slot(**kwargs) -> season_dto.Slot:
    return season_dto.Slot(id=1, season_id=1, slot_date=DAY, **kwargs)


def test_a_free_date_is_free():
    assert slot_mark(make_slot(), make_player(1)) == FREE


def test_somebody_elses_date_is_locked():
    slot = make_slot(owner=make_player(2), author_kind=season_dto.SlotAuthorKind.player)

    assert slot_mark(slot, make_player(1)) == TAKEN


def test_your_own_date_wins_over_locked():
    me = make_player(1)
    slot = make_slot(owner=me, author_kind=season_dto.SlotAuthorKind.player)

    assert slot_mark(slot, me) == MINE


def test_a_date_with_a_game_shows_the_game():
    me = make_player(1)
    slot = make_slot(
        owner=me,
        author_kind=season_dto.SlotAuthorKind.player,
        game=season_dto.LinkedGame(id=1, name="Схватка это чудо", start_at=None, number=1),
    )

    assert slot_mark(slot, me) == LINKED


def test_an_anonymous_reader_has_no_dates_of_their_own():
    slot = make_slot(owner=make_player(2), author_kind=season_dto.SlotAuthorKind.player)

    assert slot_mark(slot, None) == TAKEN


@pytest.mark.asyncio
async def test_a_marked_day_carries_its_mark():
    text = SlotDayText()

    rendered = await text.render_text(
        {"date": DAY, "data": {MARKS_KEY: {DAY.isoformat(): MINE}}},
        typing.cast(DialogManager, None),
    )

    assert rendered == f"{MINE}16"


@pytest.mark.asyncio
async def test_a_day_with_nothing_planned_is_a_plain_number():
    text = SlotDayText()

    rendered = await text.render_text(
        {"date": DAY, "data": {MARKS_KEY: {}}}, typing.cast(DialogManager, None)
    )

    assert rendered == "16"


@pytest.mark.asyncio
async def test_today_keeps_its_brackets():
    text = SlotDayText(today=True)

    rendered = await text.render_text({"date": DAY, "data": {}}, typing.cast(DialogManager, None))

    assert rendered == "[16]"


def test_a_game_planned_outside_the_schedule_says_so():
    at = datetime(2026, 5, 17, 21, 0, tzinfo=tz_game)

    rendered = render_game_log(
        GameLogEvent(
            GameLogType.GAME_PLANED,
            {"game": "Схватка это чудо", "at": "17.05.26 21:00", "in_schedule": False},
        )
    )

    assert rendered.endswith("(вне расписания сезона)")
    assert at.strftime("%d.%m.%y %H:%M") in rendered


def test_a_game_planned_on_a_date_of_the_schedule_says_nothing_extra():
    rendered = render_game_log(
        GameLogEvent(
            GameLogType.GAME_PLANED,
            {"game": "Схватка это чудо", "at": "16.05.26 21:00", "in_schedule": True},
        )
    )

    assert rendered == "Начало игры Схватка это чудо запланировано на 16.05.26 21:00"
