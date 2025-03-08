import pytest

from shvatka.core.models.dto import hints
from shvatka.core.utils import exceptions


def test_create_ok_time_hint():
    time_hint = hints.TimeHint(
        time=0,
        hint=[hints.TextHint(text="some text")],
    )
    assert time_hint.time == 0
    assert time_hint.hint == [hints.TextHint(text="some text")]


def test_create_empty_time_hint():
    with pytest.raises(exceptions.LevelError):
        hints.TimeHint(time=5, hint=[])


def test_edit_empty_time_hint():
    time_hint = hints.TimeHint(
        time=0,
        hint=[hints.TextHint(text="some text")],
    )
    with pytest.raises(exceptions.LevelError):
        time_hint.update_hint([])


def test_ok_change_time():
    time_hint = hints.TimeHint(
        time=5,
        hint=[hints.TextHint(text="some text")],
    )
    time_hint.update_time(10)
    assert time_hint.time == 10
    assert time_hint.hint == [hints.TextHint(text="some text")]


def test_change_time_for_0():
    time_hint = hints.TimeHint(
        time=0,
        hint=[hints.TextHint(text="some text")],
    )
    with pytest.raises(exceptions.LevelError):
        time_hint.update_time(5)


def test_change_time_to_0():
    time_hint = hints.TimeHint(
        time=5,
        hint=[hints.TextHint(text="some text")],
    )
    with pytest.raises(exceptions.LevelError):
        time_hint.update_time(0)
