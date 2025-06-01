import pytest

from shvatka.core.models.dto import hints
from shvatka.core.utils import exceptions


def test_update_time():
    hint = hints.TimeHint(5, [hints.TextHint(text="foo")])

    hint.update_time(10)

    assert hint.time == 10
    assert hint.hint == [hints.TextHint(text="foo")]


def test_update_hint():
    hint = hints.TimeHint(5, [hints.TextHint(text="foo")])

    hint.update_hint([hints.TextHint(text="bar")])

    assert hint.time == 5
    assert hint.hint == [hints.TextHint(text="bar")]


def test_restrict_update_time_to_0():
    hint = hints.TimeHint(5, [hints.TextHint(text="foo")])

    with pytest.raises(exceptions.LevelError):
        hint.update_time(0)


def test_restrict_update_time_from_0():
    hint = hints.TimeHint(0, [hints.TextHint(text="foo")])

    with pytest.raises(exceptions.LevelError):
        hint.update_time(5)


def test_restrict_update_to_empty_hints():
    hint = hints.TimeHint(5, [hints.TextHint(text="foo")])

    with pytest.raises(exceptions.LevelError):
        hint.update_hint([])
