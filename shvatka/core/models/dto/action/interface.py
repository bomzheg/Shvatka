from __future__ import annotations

import enum
import typing
from typing import Protocol


class Condition(Protocol):
    def check(self, action: Action, state_holder: StateHolder) -> Decision:
        raise NotImplementedError


class Action(Protocol):
    pass


class State(Protocol):
    pass


T = typing.TypeVar("T")


class StateHolder(Protocol):
    def get(self, state_class: type[T]) -> T:
        raise NotImplementedError


class Decision(Protocol):
    type: DecisionType


class DecisionType(enum.StrEnum):
    NOT_IMPLEMENTED = enum.auto()
    LEVEL_UP = enum.auto()
    SIGNIFICANT_ACTION = enum.auto()
    NO_ACTION = enum.auto()
    BONUS_TIME = enum.auto()
