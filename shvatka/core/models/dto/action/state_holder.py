from dataclasses import dataclass
from datetime import datetime

from . import TypedKeysState, SHKey, LevelTimerState
from .interface import StateHolder, T
from .. import action


@dataclass
class InMemoryKeyStateHolder(StateHolder):
    typed_correct: set[SHKey]
    all_typed: set[SHKey]

    def get(self, state_class: type[T]) -> T:
        if state_class == TypedKeysState:
            return TypedKeysState(  # type: ignore[return-value]
                typed_correct=self.typed_correct,
                all_typed=self.all_typed,
            )
        else:
            raise NotImplementedError(f"unknown state type {type(state_class)}")


@dataclass
class InMemoryTimerStateHolder(StateHolder):
    started_level_time_id: int
    current_level_time_id: int
    applied_effects: list[action.Effects]
    started_at: datetime

    def get(self, state_class: type[T]) -> T:
        if state_class == LevelTimerState:
            return LevelTimerState(  # type: ignore[return-value]
                started_level_time_id=self.started_level_time_id,
                current_level_time_id=self.current_level_time_id,
                aplied_effects=self.applied_effects,
                started_at=self.started_at,
            )
        else:
            raise NotImplementedError(f"unknown state type {type(state_class)}")
