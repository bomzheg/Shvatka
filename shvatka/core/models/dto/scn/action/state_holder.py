from dataclasses import dataclass

from . import TypedKeysState
from .interface import StateHolder, T
from shvatka.core.models.dto import scn


@dataclass
class InMemoryStateHolder(StateHolder):
    typed_correct: set[scn.SHKey]
    all_typed: set[scn.SHKey]

    def get(self, state_class: type[T]) -> T:
        if isinstance(state_class, TypedKeysState):
            return TypedKeysState(
                typed_correct=self.typed_correct,
                all_typed=self.all_typed,
            )
        else:
            raise NotImplementedError(f"unknown state type {type(state_class)}")
