import uuid
from datetime import timedelta

import pytest

from shvatka.core.models.dto.action import keys, Effects, ConditionType
from shvatka.core.models.dto import scn
from shvatka.core.models.dto import action
from shvatka.core.utils import exceptions


@pytest.fixture
def complex_conditions() -> scn.Conditions:
    return scn.Conditions(
        [
            action.KeyWinCondition({keys.SHKey("SH123"), keys.SHKey("SH321")}),
            action.KeyBonusCondition(
                {
                    keys.BonusKey(text="SHB1", bonus_minutes=1),
                    keys.BonusKey(text="SHB2", bonus_minutes=-1),
                }
            ),
            action.KeyBonusCondition({keys.BonusKey(text="SHB3", bonus_minutes=0)}),
            action.KeyWinCondition({keys.SHKey("СХ123")}),
        ]
    )


@pytest.fixture
def timer_condition() -> scn.Conditions:
    return scn.Conditions(
        [
            action.LevelTimerEffectsCondition(
                timedelta(minutes=30),
                Effects(id=uuid.uuid4(), level_up=True),
                ConditionType.EFFECTS,
            )
        ]
    )


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


@pytest.mark.skip  # TODO 128
def test_conditions_get_keys():
    c = scn.Conditions(
        [
            action.KeyWinCondition({keys.SHKey("SH123"), keys.SHKey("SH321")}),
            action.KeyWinCondition({keys.SHKey("СХ123")}),
        ]
    )
    assert c.get_keys() == {keys.SHKey("SH123"), keys.SHKey("SH321"), keys.SHKey("СХ123")}


@pytest.mark.skip  # TODO 128
def test_conditions_get_keys_with_bonus(complex_conditions: scn.Conditions):
    assert complex_conditions.get_keys() == {
        keys.SHKey("SH123"),
        keys.SHKey("SH321"),
        keys.SHKey("СХ123"),
    }


@pytest.mark.skip  # TODO 128
def test_conditions_get_bonus_keys(complex_conditions: scn.Conditions):
    assert complex_conditions.get_bonus_keys() == {
        keys.BonusKey(text="SHB1", bonus_minutes=1),
        keys.BonusKey(text="SHB2", bonus_minutes=-1),
        keys.BonusKey(text="SHB3", bonus_minutes=0),
    }


def test_conditions_duplicate_keys():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions(
            [
                action.KeyWinCondition({keys.SHKey("SH123"), keys.SHKey("SH321")}),
                action.KeyWinCondition({keys.SHKey("СХ123")}),
                action.KeyWinCondition({keys.SHKey("SH321")}),
            ]
        )


def test_conditions_duplicate_bonus_keys():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions(
            [
                action.KeyWinCondition({keys.SHKey("SH123")}),
                action.KeyBonusCondition(
                    {
                        keys.BonusKey(text="SHB1", bonus_minutes=1),
                        keys.BonusKey(text="SH123", bonus_minutes=-1),
                    }
                ),
                action.KeyBonusCondition({keys.BonusKey(text="SHB3", bonus_minutes=0)}),
            ]
        )


def test_conditions_duplicate_both_keys():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions(
            [
                action.KeyWinCondition({keys.SHKey("SH123"), keys.SHKey("SH321")}),
                action.KeyWinCondition({keys.SHKey("СХ123")}),
                action.KeyBonusCondition(
                    {
                        keys.BonusKey(text="SHB1", bonus_minutes=1),
                        keys.BonusKey(text="СХ123", bonus_minutes=-1),
                    }
                ),
                action.KeyBonusCondition({keys.BonusKey(text="SHB3", bonus_minutes=0)}),
            ]
        )


def test_conditions_two_level_up_timer():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions(
            [
                action.LevelTimerEffectsCondition(
                    timedelta(minutes=30),
                    Effects(id=uuid.uuid4(), level_up=True),
                    ConditionType.EFFECTS,
                ),
                action.LevelTimerEffectsCondition(
                    timedelta(minutes=40),
                    Effects(id=uuid.uuid4(), level_up=True),
                    ConditionType.EFFECTS,
                ),
            ]
        )


def test_conditions_two_same_effects_id_timer():
    effect_id = uuid.uuid4()
    with pytest.raises(exceptions.LevelError):
        scn.Conditions(
            [
                action.LevelTimerEffectsCondition(
                    timedelta(minutes=30),
                    Effects(id=effect_id, level_up=True),
                    ConditionType.EFFECTS,
                ),
                action.LevelTimerEffectsCondition(
                    timedelta(minutes=20),
                    Effects(id=effect_id, bonus_minutes=1),
                    ConditionType.EFFECTS,
                ),
            ]
        )


def test_conditions_effect_after_level_up_timer():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions(
            [
                action.LevelTimerEffectsCondition(
                    timedelta(minutes=30),
                    Effects(id=uuid.uuid4(), level_up=True),
                    ConditionType.EFFECTS,
                ),
                action.LevelTimerEffectsCondition(
                    timedelta(minutes=40),
                    Effects(id=uuid.uuid4(), bonus_minutes=1),
                    ConditionType.EFFECTS,
                ),
            ]
        )
