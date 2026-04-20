from __future__ import annotations

import abc
import enum
import typing
from dataclasses import dataclass
from typing import Protocol, Literal

from .effects import Effects


class ConditionType(enum.StrEnum):
    WIN_KEY = enum.auto()
    EFFECTS_KEY = enum.auto()
    EFFECTS_TIMER = enum.auto()


class Condition(Protocol):
    type: str

    def check(self, action: Action, state_holder: StateHolder) -> Decision:
        raise NotImplementedError

    def get_guids(self) -> list[str]:
        raise NotImplementedError


class Action(Protocol):
    pass


class State(Protocol):
    pass


T = typing.TypeVar("T", bound=State)


class StateHolder(Protocol):
    def get(self, state_class: type[T]) -> T:
        raise NotImplementedError


class DecisionType(enum.StrEnum):
    NOT_IMPLEMENTED = enum.auto()
    SIGNIFICANT_ACTION = enum.auto()
    EFFECTS = enum.auto()
    NO_ACTION = enum.auto()


@dataclass(kw_only=True, frozen=True)
class Decision(Protocol):
    type: DecisionType

    def is_level_up(self) -> bool:
        return False


@dataclass(kw_only=True, frozen=True)
class NoActionDecision(Decision):
    type: Literal[DecisionType.NO_ACTION] = DecisionType.NO_ACTION


@dataclass(kw_only=True, frozen=True)
class EffectsCondition(Condition, metaclass=abc.ABCMeta):
    effects: Effects

    def get_guids(self) -> list[str]:
        return self.effects.get_guids()


@dataclass(kw_only=True, frozen=True)
class EffectsDecision(Decision):
    type: typing.Literal[DecisionType.EFFECTS] = DecisionType.EFFECTS
    effects: Effects

    def is_level_up(self) -> bool:
        return self.effects.level_up


@dataclass(kw_only=True, frozen=True)
class MultipleEffectsDecision(Decision):
    type: typing.Literal[DecisionType.EFFECTS] = DecisionType.EFFECTS
    effects: list[Effects]

    def is_level_up(self) -> bool:
        return any(map(lambda e: e.level_up, self.effects))
