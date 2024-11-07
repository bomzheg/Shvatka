import enum
import typing

from .interface import Condition, Action, State, Decision, DecisionType, StateHolder
from .decisions import NotImplementedActionDecision, Decisions
from .keys import (
    SHKey,
    BonusKey,
    KeyDecision,
    KeyWinCondition,
    TypedKeyAction,
    TypedKeysState,
    BonusKeyDecision,
    KeyBonusCondition,
    WrongKeyDecision,
)
from .state_holder import InMemoryStateHolder

AnyCondition: typing.TypeAlias = KeyWinCondition | KeyBonusCondition
