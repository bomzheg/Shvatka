import pytest

from shvatka.core.models.dto import scn
from shvatka.core.utils import exceptions


def test_update_time():
    hint = scn.TimeHint(5, [scn.TextHint("foo")])

    hint.update_time(10)

    assert hint.time == 10
    assert hint.hint == [scn.TextHint("foo")]


def test_update_hint():
    hint = scn.TimeHint(5, [scn.TextHint("foo")])

    hint.update_hint([scn.TextHint("bar")])

    assert hint.time == 5
    assert hint.hint == [scn.TextHint("bar")]


def test_restrict_update_time_to_0():
    hint = scn.TimeHint(5, [scn.TextHint("foo")])

    with pytest.raises(exceptions.LevelError):
        hint.update_time(0)


def test_restrict_update_time_from_0():
    hint = scn.TimeHint(0, [scn.TextHint("foo")])

    with pytest.raises(exceptions.LevelError):
        hint.update_time(5)


def test_restrict_update_to_empty_hints():
    hint = scn.TimeHint(5, [scn.TextHint("foo")])

    with pytest.raises(exceptions.LevelError):
        hint.update_hint([])
