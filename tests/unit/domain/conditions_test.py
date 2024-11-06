import pytest

from shvatka.core.models.dto.action import keys
from shvatka.core.models.dto import scn
from shvatka.core.models.dto import action
from shvatka.core.utils import exceptions


def test_create_one_key():
    c = scn.Conditions([action.KeyWinCondition({keys.SHKey("SH321")})])
    assert len(c) == 1
    assert len(c.get_keys()) == 1
    assert len(c.get_bonus_keys()) == 0
    actual = c[0]
    assert isinstance(actual, action.KeyWinCondition)
    assert actual.keys == {keys.SHKey("SH321")}
    assert c.get_keys() == {keys.SHKey("SH321")}


def test_create_empty_condition():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions([])


def test_create_only_bonus_condition():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions([action.KeyBonusCondition({keys.BonusKey(text="SH123", bonus_minutes=1)})])

def test_conditions_get_keys():
    c = scn.Conditions([
        action.KeyWinCondition({keys.SHKey("SH123"), keys.SHKey("SH321")}),
        action.KeyWinCondition({keys.SHKey("СХ123")})
    ])
    assert c.get_keys() == {keys.SHKey("SH123"), keys.SHKey("SH321"), keys.SHKey("СХ123")}
