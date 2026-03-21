import typing

from .interface import (
    Condition,
    ConditionType,
    Action,
    State,
    Decision,
    DecisionType,
    StateHolder,
    MultipleEffectsDecision,
    NoActionDecision,
)
from .decisions import NotImplementedActionDecision, Decisions
from .keys import (
    SHKey,
    BonusKey,
    KeyDecision,
    TypedKeyDecision,
    KeyWinCondition,
    KeyCondition,
    TypedKeyAction,
    TypedKeysState,
    WrongKeyDecision,
    KeyBonusHintCondition,
    KeyEffectsDecision,
    KeyEffectsCondition,
)
from .state_holder import InMemoryKeyStateHolder, InMemoryTimerStateHolder
from .timer import (
    LevelTimerAction,
    LevelTimerState,
    LevelTimerDecision,
    LevelTimerEffectsCondition,
    LevelTimerEffectsDecision,
)
from .effects import EffectType, Effects

AnyCondition: typing.TypeAlias = (
    KeyWinCondition
    | KeyBonusHintCondition
    | KeyEffectsCondition
    | LevelTimerEffectsCondition
)
