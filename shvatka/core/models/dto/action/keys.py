import typing
from dataclasses import dataclass
from typing import Literal

from shvatka.core.models import enums
from . import StateHolder
from .decisions import NotImplementedActionDecision
from .interface import Action, State, Decision, Condition, DecisionType, ConditionType

SHKey: typing.TypeAlias = str


@dataclass(frozen=True)
class BonusKey:
    text: SHKey
    bonus_minutes: float

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


@dataclass
class KeyDecision(Decision):
    type: DecisionType
    key_type: enums.KeyType
    duplicate: bool
    key: SHKey

    def is_level_up(self) -> bool:
        return self.type == DecisionType.LEVEL_UP

    @property
    def key_text(self) -> str:
        return self.key


@dataclass
class KeyWinCondition(Condition):
    keys: set[SHKey]
    type: Literal[ConditionType.WIN_KEY] = ConditionType.WIN_KEY

    def check(self, action: Action, state_holder: StateHolder) -> Decision:
        if not isinstance(action, TypedKeyAction):
            return NotImplementedActionDecision()
        state = state_holder.get(TypedKeysState)
        type_: DecisionType
        if not self._is_correct(action):
            return WrongKeyDecision(duplicate=state.is_duplicate(action), key=action.key)
        if not state.is_duplicate(action):
            if self._is_all_typed(action, state):
                type_ = DecisionType.LEVEL_UP
            else:
                type_ = DecisionType.SIGNIFICANT_ACTION
        else:
            type_ = DecisionType.NO_ACTION
        return KeyDecision(
            type=type_,
            key_type=enums.KeyType.simple if self._is_correct(action) else enums.KeyType.wrong,
            duplicate=state.is_duplicate(action),
            key=action.key,
        )

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
class KeyBonusCondition(Condition):
    keys: set[BonusKey]
    type: Literal[ConditionType.BONUS_KEY] = ConditionType.BONUS_KEY

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

    def _get_bonus(self, action: TypedKeyAction) -> BonusKey | None:
        for bonus_key in self.keys:
            if action.key == bonus_key.text:
                return bonus_key
        return None
