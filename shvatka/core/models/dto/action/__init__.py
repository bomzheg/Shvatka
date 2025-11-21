import typing

from .interface import Condition, ConditionType, Action, State, Decision, DecisionType, StateHolder
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
    KeyWinCondition | KeyBonusCondition | KeyBonusHintCondition | LevelTimerEffectsCondition
)
