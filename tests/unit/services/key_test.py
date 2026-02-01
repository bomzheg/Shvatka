import uuid

from shvatka.core.models.dto import action
from shvatka.core.services.key import decision_to_parsed_key
from shvatka.core.models import enums, dto
from tests.utils.effects import assert_effects_equal


def test_decision_to_simple_parsed_key():
    actual = decision_to_parsed_key(
        action.TypedKeyDecision(
            type=action.DecisionType.NO_ACTION,
            key_type=enums.KeyType.simple,
            duplicate=False,
            key="SH123",
        )
    )
    assert actual.type_ == enums.KeyType.simple
    assert actual.text == "SH123"
    assert actual.effect.is_no_effects()


def test_decision_to_bonus_parsed_key():
    actual = decision_to_parsed_key(
        action.BonusKeyDecision(
            type=action.DecisionType.BONUS_TIME,
            key_type=enums.KeyType.bonus,
            duplicate=False,
            key=action.BonusKey(text="SH123", bonus_minutes=10),
        )
    )
    assert actual.type_ == enums.KeyType.bonus
    assert actual.text == "SH123"
    assert_effects_equal(actual.effect, action.Effects(id=uuid.uuid4(), bonus_minutes=10))


def test_decision_to_wrong_parsed_key():
    actual = decision_to_parsed_key(
        action.WrongKeyDecision(
            type=action.DecisionType.NO_ACTION,
            key_type=enums.KeyType.wrong,
            duplicate=False,
            key="SH123",
        )
    )
    expected = dto.ParsedKey(
        type_=enums.KeyType.wrong, text="SH123", effect=action.Effects(id=uuid.uuid4())
    )
    assert actual.type_ == expected.type_
    assert actual.text == expected.text
    assert_effects_equal(actual.effect, expected.effect)
