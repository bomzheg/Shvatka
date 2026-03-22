import abc
import typing
from abc import abstractmethod
from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

from shvatka.core.models import enums
from shvatka.core.utils.input_validation import is_key_valid
from .effects import Effects
from .decisions import NotImplementedActionDecision
from .interface import (
    Action,
    State,
    Decision,
    Condition,
    DecisionType,
    ConditionType,
    EffectsDecision,
)


if typing.TYPE_CHECKING:
    from .state_holder import StateHolder

SHKey: typing.TypeAlias = str


@dataclass(frozen=True)
class BonusKey:
    text: SHKey
    bonus_minutes: float

    def __post_init__(self):
        if not is_key_valid(self.text):
            raise ValueError
        if not (-600 < self.bonus_minutes < 60):
            raise ValueError("bonus out of available range")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BonusKey):
            return NotImplemented
        return self.text == other.text

    def __hash__(self) -> int:
        return hash(self.text)


@dataclass
class TypedKeyAction(Action):
    key: SHKey


@dataclass
class TypedKeysState(State):
    typed_correct: set[SHKey]
    all_typed: set[SHKey]

    def is_duplicate(self, action: TypedKeyAction) -> bool:
        return action.key in self.all_typed


@dataclass(kw_only=True, frozen=True)
class KeyDecision(Decision):
    duplicate: bool
    key_type: enums.KeyType

    @property
    @abstractmethod
    def key_text(self) -> str:
        raise NotImplementedError


@dataclass(kw_only=True, frozen=True)
class WrongKeyDecision(KeyDecision):
    duplicate: bool
    key: str
    type: Literal[DecisionType.NO_ACTION] = DecisionType.NO_ACTION
    key_type: typing.Literal[enums.KeyType.wrong] = enums.KeyType.wrong

    @property
    def key_text(self) -> str:
        return self.key


@dataclass(kw_only=True, frozen=True)
class TypedKeyDecision(KeyDecision):
    type: DecisionType
    key_type: enums.KeyType
    duplicate: bool
    key: SHKey

    @property
    def key_text(self) -> str:
        return self.key


class KeyCondition(Condition, metaclass=abc.ABCMeta):
    def get_keys(self) -> set[SHKey]:
        raise NotImplementedError

    def _is_correct(self, action: TypedKeyAction) -> bool:
        return action.key in self.get_keys()

    def _is_all_typed(self, action: TypedKeyAction, state: TypedKeysState) -> bool:
        return self.get_keys() == {*state.typed_correct, action.key}


@dataclass
class KeyWinCondition(KeyCondition):
    keys: set[SHKey]  # all keys are required
    type: Literal["WIN_KEY"] = ConditionType.WIN_KEY.name
    next_level: str | None = None

    def check(self, action: Action, state_holder: "StateHolder") -> Decision:
        if not isinstance(action, TypedKeyAction):
            return NotImplementedActionDecision()
        state = state_holder.get(TypedKeysState)
        type_: DecisionType
        if not self._is_correct(action):
            return WrongKeyDecision(duplicate=state.is_duplicate(action), key=action.key)
        if state.is_duplicate(action):
            type_ = DecisionType.NO_ACTION
        elif self._is_all_typed(action, state):
            return KeyEffectsDecision(
                type=DecisionType.EFFECTS,
                key_type=self._get_key_type(action),  # TODO always simple
                duplicate=state.is_duplicate(action),
                key=action.key,
                effects=Effects(
                    id=uuid4(),
                    level_up=True,
                    next_level=self.next_level,
                ),
            )
        else:
            type_ = DecisionType.SIGNIFICANT_ACTION
        return TypedKeyDecision(
            type=type_,
            key_type=self._get_key_type(action),  # TODO always simple
            duplicate=state.is_duplicate(action),
            key=action.key,
        )

    def get_keys(self) -> set[SHKey]:
        return self.keys

    def _get_key_type(self, action: TypedKeyAction):
        return enums.KeyType.simple if self._is_correct(action) else enums.KeyType.wrong


@dataclass(kw_only=True, frozen=True)
class KeyEffectsDecision(TypedKeyDecision, EffectsDecision):
    pass


@dataclass
class KeyEffectsCondition(KeyCondition):
    keys: set[SHKey]  # all keys are required
    effects: Effects
    type: Literal["EFFECTS_KEY"] = ConditionType.EFFECTS_KEY.name

    def check(self, action: Action, state_holder: "StateHolder") -> Decision:
        if not isinstance(action, TypedKeyAction):
            return NotImplementedActionDecision()
        state = state_holder.get(TypedKeysState)
        if not self._is_correct(action):
            return WrongKeyDecision(duplicate=state.is_duplicate(action), key=action.key)
        if state.is_duplicate(action):
            type_ = DecisionType.NO_ACTION
        elif self._is_all_typed(action, state):
            return KeyEffectsDecision(
                key_type=self._get_key_type(action),
                duplicate=state.is_duplicate(action),
                key=action.key,
                effects=self.effects,
                type=DecisionType.EFFECTS,
            )
        else:
            type_ = DecisionType.SIGNIFICANT_ACTION
        return TypedKeyDecision(
            type=type_,
            key_type=self._get_key_type(action),
            duplicate=state.is_duplicate(action),
            key=action.key,
        )

    def get_keys(self) -> set[SHKey]:
        return self.keys

    def _get_key_type(self, action: TypedKeyAction):
        return enums.KeyType.effects if self._is_correct(action) else enums.KeyType.wrong
