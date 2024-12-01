from shvatka.core.models.dto import action
from shvatka.core.services.key import decision_to_parsed_key
from shvatka.core.models import enums, dto


def test_decision_to_simple_parsed_key():
    assert decision_to_parsed_key(
        action.KeyDecision(
            type=action.DecisionType.NO_ACTION,
            key_type=enums.KeyType.simple,
            duplicate=False,
            key="SH123",
        )
    ) == dto.ParsedKey(type_=enums.KeyType.simple, text="SH123")


def test_decision_to_bonus_parsed_key():
    assert decision_to_parsed_key(
        action.BonusKeyDecision(
            type=action.DecisionType.BONUS_TIME,
            key_type=enums.KeyType.bonus,
            duplicate=False,
            key=action.BonusKey(text="SH123", bonus_minutes=10),
        )
    ) == dto.ParsedBonusKey(type_=enums.KeyType.bonus, text="SH123", bonus_minutes=10)


def test_decision_to_wrong_parsed_key():
    assert decision_to_parsed_key(
        action.WrongKeyDecision(
            type=action.DecisionType.NO_ACTION,
            key_type=enums.KeyType.wrong,
            duplicate=False,
            key="SH123",
        )
    ) == dto.ParsedKey(type_=enums.KeyType.wrong, text="SH123")
