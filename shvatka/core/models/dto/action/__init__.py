import typing

from .decisions import Decisions, NotImplementedActionDecision
from .effects import Effects
from .interface import (
    Action,
    Condition,
    ConditionType,
    Decision,
    DecisionType,
    EffectsCondition,
    MultipleEffectsDecision,
    NoActionDecision,
    State,
    StateHolder,
)
from .keys import (
    BonusKey,
    KeyCondition,
    KeyDecision,
    KeyEffectsCondition,
    KeyEffectsDecision,
    KeyWinCondition,
    SHKey,
    TypedKeyAction,
    TypedKeyDecision,
    TypedKeysState,
    WrongKeyDecision,
)
from .state_holder import InMemoryKeyStateHolder, InMemoryTimerStateHolder
from .timer import (
    LevelTimerAction,
    LevelTimerDecision,
    LevelTimerEffectsCondition,
    LevelTimerEffectsDecision,
    LevelTimerState,
)

AnyCondition: typing.TypeAlias = KeyWinCondition | KeyEffectsCondition | LevelTimerEffectsCondition
