import typing

from .interface import Condition, Action, State, Decision, DecisionType, StateHolder
from .decisions import NotImplementedActionDecision, Decisions
from .keys import (
    SHKey,
    BonusKey,
    KeyDecision,
    TypedKeyDecision,
    KeyWinCondition,
    TypedKeyAction,
    TypedKeysState,
    BonusKeyDecision,
    KeyBonusCondition,
    WrongKeyDecision,
    LevelUpDecision,
    BonusHintKeyDecision,
    KeyBonusHintCondition,
)
from .state_holder import InMemoryStateHolder

AnyCondition: typing.TypeAlias = KeyWinCondition | KeyBonusCondition
