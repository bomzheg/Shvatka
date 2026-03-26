import uuid
from datetime import timedelta

import pytest

from shvatka.core.models.dto.action import keys, Effects
from shvatka.core.models.dto import scn
from shvatka.core.models.dto import action
from shvatka.core.utils import exceptions


def bonus_effect(bonus_minutes: int) -> action.Effects:
    return Effects(
        id=uuid.uuid4(),
        bonus_minutes=bonus_minutes,
    )


@pytest.fixture
def timer_condition() -> scn.Conditions:
    return scn.Conditions(
        [
            action.LevelTimerEffectsCondition(
                action_time=30,
                effects=Effects(id=uuid.uuid4(), level_up=True),
            )
        ]
    )


def test_create_one_key():
    c = scn.Conditions([action.KeyWinCondition({keys.SHKey("SH321")})])
    assert len(c) == 1
    assert len(c.get_keys()) == 1
    actual = c[0]
    assert isinstance(actual, action.KeyWinCondition)
    assert actual.keys == {keys.SHKey("SH321")}
    assert c.get_keys() == {keys.SHKey("SH321")}


def test_create_empty_condition():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions([])


def test_create_only_bonus_condition():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions([action.KeyEffectsCondition(keys={"SH123"}, effects=bonus_effect(1))])


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
                action.KeyEffectsCondition(keys={"SHB1"}, effects=bonus_effect(1)),
                action.KeyEffectsCondition(keys={"SH123"}, effects=bonus_effect(-1)),
                action.KeyEffectsCondition(keys={"SHB3"}, effects=bonus_effect(0)),
            ]
        )


def test_conditions_duplicate_both_keys():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions(
            [
                action.KeyWinCondition({keys.SHKey("SH123"), keys.SHKey("SH321")}),
                action.KeyWinCondition({keys.SHKey("СХ123")}),
                action.KeyEffectsCondition(keys={"SHB1"}, effects=bonus_effect(1)),
                action.KeyEffectsCondition(keys={"СХ123"}, effects=bonus_effect(-1)),
                action.KeyEffectsCondition(keys={"SHB3"}, effects=bonus_effect(0)),
            ]
        )


def test_conditions_just_level_up():
    conditions = scn.Conditions(
        [
            action.LevelTimerEffectsCondition(
                action_time=30,
                effects=Effects(id=uuid.uuid4(), level_up=True),
            ),
        ]
    )
    assert conditions.get_keys() == set()
    assert conditions.get_force_level_up_time() == timedelta(minutes=30)


def test_conditions_two_level_up_timer():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions(
            [
                action.LevelTimerEffectsCondition(
                    action_time=30,
                    effects=Effects(id=uuid.uuid4(), level_up=True),
                ),
                action.LevelTimerEffectsCondition(
                    action_time=40,
                    effects=Effects(id=uuid.uuid4(), level_up=True),
                ),
            ]
        )


def test_conditions_two_same_effects_id_timer():
    effect_id = uuid.uuid4()
    with pytest.raises(exceptions.LevelError):
        scn.Conditions(
            [
                action.LevelTimerEffectsCondition(
                    action_time=30,
                    effects=Effects(id=effect_id, level_up=True),
                ),
                action.LevelTimerEffectsCondition(
                    action_time=20,
                    effects=Effects(id=effect_id, bonus_minutes=1),
                ),
            ]
        )


def test_conditions_effect_after_level_up_timer():
    with pytest.raises(exceptions.LevelError):
        scn.Conditions(
            [
                action.LevelTimerEffectsCondition(
                    action_time=30,
                    effects=Effects(id=uuid.uuid4(), level_up=True),
                ),
                action.LevelTimerEffectsCondition(
                    action_time=40,
                    effects=Effects(id=uuid.uuid4(), bonus_minutes=1),
                ),
            ]
        )
