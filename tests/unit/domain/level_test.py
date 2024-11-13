import pytest

from shvatka.core.models import enums
from shvatka.core.models.dto import scn, action


@pytest.fixture
def hints() -> scn.HintsList:
    return scn.HintsList(
        [
            scn.TimeHint(time=0, hint=[scn.TextHint("hint")]),
            scn.TimeHint(time=5, hint=[scn.TextHint("other hint")]),
        ]
    )


@pytest.fixture
def level_one_key(hints: scn.HintsList) -> scn.LevelScenario:
    return scn.LevelScenario(
        id="test1",
        time_hints=hints,
        conditions=scn.Conditions(
            [
                action.KeyWinCondition({"SH123"}),
                action.KeyBonusCondition({action.BonusKey(text="SHB1", bonus_minutes=1)}),
            ]
        ),
    )


@pytest.fixture
def level_three_keys(hints: scn.HintsList) -> scn.LevelScenario:
    return scn.LevelScenario(
        id="test2",
        time_hints=hints,
        conditions=scn.Conditions(
            [
                action.KeyWinCondition({"SH123", "SH321", "СХ123"}),
                action.KeyBonusCondition({action.BonusKey(text="SHB1", bonus_minutes=1)}),
            ]
        ),
    )


def test_win_level_single_key(level_one_key: scn.LevelScenario):
    decision = level_one_key.check(
        action.TypedKeyAction("SH123"), action.InMemoryStateHolder(set(), set())
    )

    assert isinstance(decision, action.KeyDecision)
    assert decision.key == "SH123"
    assert decision.key_text == "SH123"
    assert decision.key_type == enums.KeyType.simple
    assert decision.type == action.DecisionType.LEVEL_UP
    assert decision.is_level_up()
    assert not decision.duplicate


def test_wrong_level_single_key(level_one_key: scn.LevelScenario):
    decision = level_one_key.check(
        action.TypedKeyAction("SHWRONG"), action.InMemoryStateHolder(set(), set())
    )

    assert isinstance(decision, action.WrongKeyDecision)
    assert decision.key == "SHWRONG"
    assert decision.key_text == "SHWRONG"
    assert decision.key_type == enums.KeyType.wrong
    assert decision.type == action.DecisionType.NO_ACTION
    assert not decision.duplicate


def test_duplicate_wrong_level_single_key(level_one_key: scn.LevelScenario):
    decision = level_one_key.check(
        action.TypedKeyAction("SHWRONG"), action.InMemoryStateHolder(set(), {"SHWRONG"})
    )

    assert isinstance(decision, action.WrongKeyDecision)
    assert decision.key == "SHWRONG"
    assert decision.key_text == "SHWRONG"
    assert decision.key_type == enums.KeyType.wrong
    assert decision.type == action.DecisionType.NO_ACTION
    assert decision.duplicate


def test_bonus_level_single_key(level_one_key: scn.LevelScenario):
    decision = level_one_key.check(
        action.TypedKeyAction("SHB1"), action.InMemoryStateHolder(set(), {"SHWRONG"})
    )

    assert isinstance(decision, action.BonusKeyDecision)
    assert decision.key.text == "SHB1"
    assert decision.key.bonus_minutes == 1
    assert decision.key_text == "SHB1"
    assert decision.key_type == enums.KeyType.bonus
    assert decision.type == action.DecisionType.BONUS_TIME
    assert not decision.duplicate


def test_duplicate_bonus_level_single_key(level_one_key: scn.LevelScenario):
    decision = level_one_key.check(
        action.TypedKeyAction("SHB1"), action.InMemoryStateHolder(set(), {"SHWRONG", "SHB1"})
    )

    assert isinstance(decision, action.BonusKeyDecision)
    assert decision.key.text == "SHB1"
    assert decision.key.bonus_minutes == 1
    assert decision.key_text == "SHB1"
    assert decision.key_type == enums.KeyType.bonus
    assert decision.type == action.DecisionType.BONUS_TIME
    assert decision.duplicate


def test_second_key_of_three(level_three_keys: scn.LevelScenario):
    decision = level_three_keys.check(
        action.TypedKeyAction("SH123"), action.InMemoryStateHolder({"SH321"}, {"SH321"})
    )

    assert isinstance(decision, action.KeyDecision)
    assert decision.key == "SH123"
    assert decision.key_text == "SH123"
    assert decision.key_type == enums.KeyType.simple
    assert decision.type == action.DecisionType.SIGNIFICANT_ACTION
    assert not decision.is_level_up()
    assert not decision.duplicate


def test_duplicate_second_key_of_three(level_three_keys: scn.LevelScenario):
    decision = level_three_keys.check(
        action.TypedKeyAction("SH123"),
        action.InMemoryStateHolder({"SH321", "SH123"}, {"SH321", "SH123"}),
    )

    assert isinstance(decision, action.KeyDecision)
    assert decision.key == "SH123"
    assert decision.key_text == "SH123"
    assert decision.key_type == enums.KeyType.simple
    assert decision.type == action.DecisionType.NO_ACTION
    assert not decision.is_level_up()
    assert decision.duplicate


def test_third_key_of_three(level_three_keys: scn.LevelScenario):
    decision = level_three_keys.check(
        action.TypedKeyAction("SH123"),
        action.InMemoryStateHolder({"SH321", "СХ123"}, {"SH321", "СХ123"}),
    )

    assert isinstance(decision, action.KeyDecision)
    assert decision.key == "SH123"
    assert decision.key_text == "SH123"
    assert decision.key_type == enums.KeyType.simple
    assert decision.type == action.DecisionType.LEVEL_UP
    assert decision.is_level_up()
    assert not decision.duplicate
