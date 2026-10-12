import logging
import uuid

import pytest

from shvatka.core.models import enums
from shvatka.core.models.dto import action, hints, scn

# a look-alike character is invisible in the source, so it is spelled by its
# code point: the level below is authored in cyrillic, the player types latin
CYRILLIC_KA = "\u041a"  # looks like latin K
CYRILLIC_O = "\u041e"  # looks like latin O
CYRILLIC_TE = "\u0422"  # looks like latin T
CYRILLIC_IE = "\u0415"  # looks like latin E
CYRILLIC_IO = "\u0401"  # cyrillic io

AUTHORED_KEY = f"SH{CYRILLIC_KA}{CYRILLIC_O}{CYRILLIC_TE}"
TYPED_KEY = "SHKOT"
AUTHORED_BONUS_KEY = f"SH{CYRILLIC_IO}1"
TYPED_BONUS_KEY = f"SH{CYRILLIC_IE}1"


@pytest.fixture
def hints_() -> scn.HintsList:
    return scn.HintsList([hints.TimeHint(time=0, hint=[hints.TextHint(text="hint")])])


@pytest.fixture
def level(hints_: scn.HintsList) -> scn.LevelScenario:
    return scn.LevelScenario(
        id="folding",
        time_hints=hints_,
        conditions=scn.Conditions(
            [
                action.KeyWinCondition({AUTHORED_KEY, "SH100"}),
                action.KeyEffectsCondition(
                    keys={AUTHORED_BONUS_KEY},
                    effects=action.Effects(id=uuid.uuid4(), bonus_minutes=1),
                ),
            ]
        ),
        __model_version__=1,
    )


def test_look_alike_key_is_correct(level: scn.LevelScenario):
    decision = level.check(
        action.TypedKeyAction(TYPED_KEY), action.InMemoryKeyStateHolder(set(), set())
    )

    assert isinstance(decision, action.TypedKeyDecision)
    assert decision.key_type == enums.KeyType.simple
    assert decision.type == action.DecisionType.SIGNIFICANT_ACTION
    assert not decision.duplicate
    assert decision.key == TYPED_KEY, "the key is logged as it was typed"


def test_look_alike_key_completes_the_level(level: scn.LevelScenario):
    decision = level.check(
        action.TypedKeyAction("SHI0O"),  # latin I and O for the digits of SH100
        action.InMemoryKeyStateHolder({TYPED_KEY}, {TYPED_KEY}),
    )

    assert isinstance(decision, action.KeyEffectsDecision)
    assert decision.is_level_up()


def test_look_alike_key_is_a_duplicate(level: scn.LevelScenario):
    decision = level.check(
        action.TypedKeyAction(TYPED_KEY),
        action.InMemoryKeyStateHolder({AUTHORED_KEY}, {AUTHORED_KEY}),
    )

    assert isinstance(decision, action.TypedKeyDecision)
    assert decision.type == action.DecisionType.NO_ACTION
    assert decision.duplicate
    assert not decision.is_level_up()


def test_look_alike_effects_key_is_correct(level: scn.LevelScenario):
    decision = level.check(
        action.TypedKeyAction(TYPED_BONUS_KEY), action.InMemoryKeyStateHolder(set(), set())
    )

    assert isinstance(decision, action.KeyEffectsDecision)
    assert decision.key_type == enums.KeyType.effects
    assert decision.effects.bonus_minutes == 1


def test_other_key_is_still_wrong(level: scn.LevelScenario):
    decision = level.check(
        action.TypedKeyAction("SHKOD"), action.InMemoryKeyStateHolder(set(), set())
    )

    assert isinstance(decision, action.WrongKeyDecision)
    assert decision.key_type == enums.KeyType.wrong


def test_confusable_level_keys_are_logged_not_rejected(caplog: pytest.LogCaptureFixture):
    with caplog.at_level(logging.WARNING):
        conditions = scn.Conditions([action.KeyWinCondition({AUTHORED_KEY, TYPED_KEY})])

    assert conditions.get_keys() == {AUTHORED_KEY, TYPED_KEY}
    assert "look-alike" in caplog.text


def test_distinct_level_keys_are_not_reported(caplog: pytest.LogCaptureFixture):
    with caplog.at_level(logging.WARNING):
        scn.Conditions([action.KeyWinCondition({TYPED_KEY, "SHKOD"})])

    assert "look-alike" not in caplog.text
