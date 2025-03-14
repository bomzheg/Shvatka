import typing
from dataclasses import dataclass
from typing import Literal

from shvatka.core.models import enums
from shvatka.core.utils.input_validation import is_key_valid
from . import StateHolder
from .decisions import NotImplementedActionDecision
from .interface import (
    Action,
    State,
    Decision,
    Condition,
    DecisionType,
    ConditionType,
    LevelUpDecision,
)

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


@dataclass
class WrongKeyDecision(Decision):
    duplicate: bool
    key: str
    type: Literal[DecisionType.NO_ACTION] = DecisionType.NO_ACTION
    key_type: typing.Literal[enums.KeyType.wrong] = enums.KeyType.wrong

    @property
    def key_text(self) -> str:
        return self.key


@dataclass(kw_only=True)
class KeyDecision(Decision):
    type: DecisionType
    key_type: enums.KeyType
    duplicate: bool
    key: SHKey

    @property
    def key_text(self) -> str:
        return self.key


@dataclass(kw_only=True)
class LevelUpKeyDecision(KeyDecision, LevelUpDecision):
    type: typing.Literal[DecisionType.LEVEL_UP] = DecisionType.LEVEL_UP
    next_level: str | None = None


class KeyCondition(Condition):
    def get_keys(self) -> set[SHKey]:
        raise NotImplementedError


@dataclass
class KeyWinCondition(KeyCondition):
    keys: set[SHKey]
    type: Literal["WIN_KEY"] = ConditionType.WIN_KEY.name
    next_level: str | None = None

    def check(self, action: Action, state_holder: StateHolder) -> Decision:
        if not isinstance(action, TypedKeyAction):
            return NotImplementedActionDecision()
        state = state_holder.get(TypedKeysState)
        type_: DecisionType
        if not self._is_correct(action):
            return WrongKeyDecision(duplicate=state.is_duplicate(action), key=action.key)
        if not state.is_duplicate(action):
            if self._is_all_typed(action, state):
                return LevelUpKeyDecision(
                    key_type=self._get_key_type(action),  # TODO always simple
                    duplicate=state.is_duplicate(action),
                    key=action.key,
                    next_level=self.next_level,
                )
            else:
                type_ = DecisionType.SIGNIFICANT_ACTION
        else:
            type_ = DecisionType.NO_ACTION
        return KeyDecision(
            type=type_,
            key_type=self._get_key_type(action),  # TODO always simple
            duplicate=state.is_duplicate(action),
            key=action.key,
        )

    def get_keys(self) -> set[SHKey]:
        return self.keys

    def _get_key_type(self, action: TypedKeyAction):
        return enums.KeyType.simple if self._is_correct(action) else enums.KeyType.wrong

    def _is_correct(self, action: TypedKeyAction) -> bool:
        return action.key in self.keys

    def _is_all_typed(self, action: TypedKeyAction, state: TypedKeysState) -> bool:
        return self.keys == {*state.typed_correct, action.key}


@dataclass
class BonusKeyDecision(Decision):
    type: DecisionType
    key_type: enums.KeyType
    duplicate: bool
    key: BonusKey

    @property
    def key_text(self) -> str:
        return self.key.text


@dataclass
class KeyBonusCondition(KeyCondition):
    keys: set[BonusKey]
    type: Literal["BONUS_KEY"] = ConditionType.BONUS_KEY.name

    def check(self, action: Action, state_holder: StateHolder) -> Decision:
        if not isinstance(action, TypedKeyAction):
            return NotImplementedActionDecision()
        state = state_holder.get(TypedKeysState)
        bonus = self._get_bonus(action)
        if bonus is None:
            return WrongKeyDecision(duplicate=state.is_duplicate(action), key=action.key)
        return BonusKeyDecision(
            type=DecisionType.BONUS_TIME,
            key_type=enums.KeyType.bonus,
            duplicate=state.is_duplicate(action),
            key=bonus,
        )

    def get_keys(self) -> set[SHKey]:
        return {key.text for key in self.keys}

    def _get_bonus(self, action: TypedKeyAction) -> BonusKey | None:
        for bonus_key in self.keys:
            if action.key == bonus_key.text:
                return bonus_key
        return None
