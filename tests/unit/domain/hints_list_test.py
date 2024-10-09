import pytest

from shvatka.core.models.dto import scn
from shvatka.core.utils import exceptions


def test_add_hint():
    hint = scn.TimeHint(0, [scn.TextHint(text="foo")])
    hints_old = scn.HintsList([hint])

    hints_new = hints_old.replace(
        hint, scn.TimeHint(0, [scn.TextHint(text="foo"), scn.TextHint("bar")])
    )

    assert len(hints_new) == 1
    assert len(hints_new.hints) == 1
    assert hints_new[0].time == 0
    assert len(hints_new[0].hint) == 2
    assert hints_new.hints_count == 2
    assert hints_new[0].hint == [scn.TextHint(text="foo"), scn.TextHint(text="bar")]


def test_change_time():
    hint = scn.TimeHint(5, [scn.TextHint(text="bar")])
    hints_old = scn.HintsList([scn.TimeHint(0, [scn.TextHint(text="foo")]), hint])

    hints_new = hints_old.replace(hint, scn.TimeHint(6, [scn.TextHint(text="bar")]))

    assert len(hints_new) == 2
    assert len(hints_new.hints) == 2
    assert hints_new[0].time == 0
    assert hints_new[1].time == 6
    assert len(hints_new[1].hint) == 1
    assert hints_new[1].hint[0] == scn.TextHint(text="bar")


def test_change_to_time_0():
    hint = scn.TimeHint(5, [scn.TextHint(text="bar")])
    hints_old = scn.HintsList([scn.TimeHint(0, [scn.TextHint(text="foo")]), hint])

    hints_new = hints_old.replace(hint, scn.TimeHint(0, [scn.TextHint(text="bar")]))

    assert len(hints_new) == 1
    assert len(hints_new.hints) == 1
    assert hints_new[0].time == 0
    assert len(hints_new[0].hint) == 2
    assert hints_new.hints_count == 2
    assert hints_new[0].hint == [scn.TextHint(text="foo"), scn.TextHint(text="bar")]


def test_restrict_change_time_0():
    hint = scn.TimeHint(0, [scn.TextHint(text="bar")])
    hints_old = scn.HintsList([hint, scn.TimeHint(5, [scn.TextHint(text="foo")])])

    with pytest.raises(exceptions.LevelError):
        hints_old.replace(hint, scn.TimeHint(6, [scn.TextHint(text="bar")]))


def test_replace_to_empty():
    hint = scn.TimeHint(5, [scn.TextHint(text="bar")])
    hints_old = scn.HintsList([scn.TimeHint(0, [scn.TextHint(text="foo")]), hint])

    with pytest.raises(exceptions.LevelError):
        hints_old.replace(hint, scn.TimeHint(5, []))
