from dataclasses import dataclass

from . import TypedKeysState, SHKey
from .interface import StateHolder, T


@dataclass
class InMemoryStateHolder(StateHolder):
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
