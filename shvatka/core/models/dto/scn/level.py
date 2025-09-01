import logging
from collections.abc import Sequence, Iterable
from dataclasses import dataclass
from datetime import timedelta
from typing import overload, Literal

from shvatka.core.models.dto import action, hints
from shvatka.core.models.dto.hints import TimeHint, AnyHint
from shvatka.core.models.dto.hints.time_hint import EnumeratedTimeHint
from shvatka.core.utils import exceptions
from shvatka.core.models.dto.action import (
    Action,
    Decision,
    StateHolder,
    DecisionType,
    Decisions,
    TypedKeyDecision,
    KeyBonusCondition,
    NotImplementedActionDecision,
    BonusKeyDecision,
    AnyCondition,
)
from shvatka.core.models.dto.action.keys import (
    SHKey,
    KeyWinCondition,
    TypedKeyAction,
    WrongKeyDecision,
    BonusKey,
    KeyCondition,
)

logger = logging.getLogger(__name__)


class HintsList(Sequence[TimeHint]):
    def __init__(self, hints_: list[TimeHint]):
        self.verify(hints_)
        self.hints = hints_

    @classmethod
    def parse(cls, hints_: list[TimeHint]):
        return cls(cls.normalize(hints_))

    @staticmethod
    def normalize(hints_: list[TimeHint]) -> list[TimeHint]:
        hint_map: dict[int, list[AnyHint]] = {}
        for hint in hints_:
            if not hint.hint:
                continue
            hint_map.setdefault(hint.time, []).extend(hint.hint)
        return [TimeHint(k, v) for k, v in sorted(hint_map.items(), key=lambda x: x[0])]

    @staticmethod
    def verify(hints_: Iterable[TimeHint]) -> None:
        current_time = -1
        times: set[int] = set()
        for hint in hints_:
            if hint.time in times:
                raise exceptions.LevelError(
                    text=f"Contains multiple times hints for time {hint.time}"
                )
            if hint.time <= current_time:
                raise exceptions.LevelError(text="hints are not sorted")
            current_time = hint.time
            times.add(hint.time)
            if not hint.hint:
                raise exceptions.LevelError(text=f"There is no hint for time {hint.time}")
        if 0 not in times:
            raise exceptions.LevelError(text="There is no hint for 0 min")

    def get_hint_by_time(self, time: timedelta) -> EnumeratedTimeHint:
        hint = self.hints[0]
        number = 0
        for i, h in enumerate(self.hints):
            if timedelta(minutes=h.time) < time:
                hint = h
                number = i
            else:
                break
        return EnumeratedTimeHint(time=hint.time, hint=hint.hint, number=number)

    def get_hints_for_timedelta(self, delta: timedelta) -> list[TimeHint]:
        minutes = delta.total_seconds() // 60
        return [th for th in self.hints if th.time <= minutes]

    def replace(self, old: TimeHint, new: TimeHint) -> "HintsList":
        old_index = self._index(old)
        result = self.hints[0:old_index] + self.hints[old_index + 1 :] + [new]
        return self.__class__(self.normalize(result))

    def delete(self, old: TimeHint) -> "HintsList":
        old_index = self._index(old)
        result = self.hints[0:old_index] + self.hints[old_index + 1 :]
        return self.__class__(self.normalize(result))

    @property
    def hints_count(self) -> int:
        return sum(time_hint.hints_count for time_hint in self.hints)

    def _index(self, old: TimeHint) -> int:
        for i, hint in enumerate(self.hints):
            if hint.time == old.time:
                old_index = i
                break
        else:
            old_index = None
        if old_index is None:
            raise exceptions.LevelError(
                text=f"can't replace, there is no hints for time {old.time}"
            )
        return old_index

    @overload
    def __getitem__(self, index: int) -> TimeHint:
        return self.hints[index]

    @overload
    def __getitem__(self, index: slice) -> Sequence[TimeHint]:
        return self.hints[index]

    def __getitem__(self, index):
        return self.hints[index]

    def __len__(self):
        return len(self.hints)

    def __eq__(self, other):
        if isinstance(other, HintsList):
            return self.hints == other.hints
        if isinstance(other, list):
            return self.hints == other
        return NotImplemented

    def __repr__(self):
        return repr(self.hints)


class Conditions(Sequence[AnyCondition]):
    def __init__(self, conditions: Sequence[AnyCondition]):
        self.validate(conditions)
        self.conditions: Sequence[AnyCondition] = conditions

    @staticmethod
    def validate(conditions: Sequence[AnyCondition]) -> None:  # noqa: C901,PLR0912
        keys: set[str] = set()
        win_conditions = []
        most_time: timedelta | None = None
        timers: list[action.LevelTimerCondition] = []
        for c in conditions:
            if isinstance(c, KeyCondition):
                if isinstance(c, KeyWinCondition):
                    win_conditions.append(c)
                if keys.intersection(c.get_keys()):
                    raise exceptions.LevelError(
                        text="keys exists multiple times",
                        confidential=f"{keys.intersection(c.keys)}",
                    )
                keys = keys.union(c.get_keys())
            if isinstance(c, action.LevelTimerCondition):
                if isinstance(c, action.LevelTimerWinCondition):
                    if most_time is not None:
                        raise exceptions.LevelError(
                            text="winning timer condition exists multiple times",
                        )
                    most_time = c.action_time
                    continue
                timers.append(c)
        if not win_conditions:
            raise exceptions.LevelError(text="There is no win condition")
        if all(c.next_level is not None for c in win_conditions):
            raise exceptions.LevelError(
                text="At least one win condition should be simple (without routing (next_level))"
            )
        # TODO #128 next is temporary restriction. we should allow multiple times
        if (count := len([c for c in win_conditions if c.next_level is None])) != 1:
            raise exceptions.LevelError(
                text=f"Default win condition must be exactly once, got {count}"
            )
        if most_time is not None:
            for timer in timers:
                if timer.get_action_time() > most_time:
                    raise exceptions.LevelError(
                        text="all timers should be less or equal than level win time",
                        confidential=f"win time={most_time}, timer={timer.get_action_time()}",
                    )

    def replace_bonus_keys(self, bonus_keys: set[action.BonusKey]) -> "Conditions":
        other_conditions = [
            c for c in self.conditions if not isinstance(c, action.KeyBonusCondition)
        ]
        if not bonus_keys:
            return Conditions(other_conditions)
        return Conditions([*other_conditions, action.KeyBonusCondition(bonus_keys)])

    def replace_default_keys(self, keys: set[action.SHKey]) -> "Conditions":
        other_conditions = [
            c
            for c in self.conditions
            if not isinstance(c, action.KeyWinCondition) or c.next_level is not None
        ]
        return Conditions([*other_conditions, action.KeyWinCondition(keys)])

    def replace_bonus_hint_conditions(
        self, conditions: list[action.KeyBonusHintCondition]
    ) -> "Conditions":
        other_conditions = [
            c for c in self.conditions if not isinstance(c, action.KeyBonusHintCondition)
        ]
        return Conditions([*other_conditions, *conditions])

    def replace_routed_conditions(self, conditions: list[action.KeyWinCondition]) -> "Conditions":
        other_conditions = [
            c
            for c in self.conditions
            if not isinstance(c, action.KeyWinCondition) or c.next_level is None
        ]
        return Conditions([*other_conditions, *conditions])

    def get_keys(self) -> set[str]:
        result: set[SHKey] = set()
        for condition in self.conditions:
            if isinstance(condition, KeyWinCondition):
                result = result.union(condition.keys)
        return result

    def get_bonus_keys(self) -> set[BonusKey]:
        result: set[BonusKey] = set()
        for condition in self.get_bonus_conditions():
            result = result.union(condition.keys)
        return result

    def get_bonus_hints_conditions(self) -> list[action.KeyBonusHintCondition]:
        return [c for c in self.conditions if isinstance(c, action.KeyBonusHintCondition)]

    def get_routed_conditions(self) -> list[action.KeyWinCondition]:
        return [
            c
            for c in self.conditions
            if isinstance(c, action.KeyWinCondition) and c.next_level is not None
        ]

    def get_bonus_conditions(self) -> list[action.KeyBonusCondition]:
        return [c for c in self.conditions if isinstance(c, action.KeyBonusCondition)]

    def get_default_key_conditions(self) -> list[action.KeyWinCondition]:
        return [
            c
            for c in self.conditions
            if isinstance(c, action.KeyWinCondition) and c.next_level is None
        ]

    def get_default_key_condition(self) -> action.KeyWinCondition:
        """TODO #128"""
        return self.get_default_key_conditions()[0]

    def get_types_count(self) -> int:
        result = 0
        if self.get_bonus_keys():
            result += 1
        if self.get_bonus_hints_conditions():
            result += 1
        if self.get_routed_conditions():
            result += 1
        return result

    @property
    def hints_count(self) -> int:
        return len(self.get_hints())

    def get_hints(self) -> list[hints.AnyHint]:
        acc = []
        for c in self.conditions:
            if not isinstance(c, action.KeyBonusHintCondition):
                continue
            acc.extend(c.bonus_hint)
        return acc

    @overload
    def __getitem__(self, index: int) -> AnyCondition:
        return self.conditions[index]

    @overload
    def __getitem__(self, index: slice) -> Sequence[AnyCondition]:
        return self.conditions[index]

    def __getitem__(self, index):
        return self.conditions[index]

    def __len__(self):
        return len(self.conditions)

    def __repr__(self):
        return repr(self.conditions)

    def __eq__(self, other):
        if not isinstance(other, Conditions):
            return NotImplemented
        return self.conditions == other.conditions


@dataclass
class LevelScenario:
    id: str
    time_hints: HintsList
    conditions: Conditions
    __model_version__: Literal[1]

    def __post_init__(self):
        if not self.conditions:
            raise exceptions.LevelError(text="no win conditions are present")

    def get_hint(self, hint_number: int) -> TimeHint:
        return self.time_hints[hint_number]

    def get_hint_by_time(self, time: timedelta) -> EnumeratedTimeHint:
        return self.time_hints.get_hint_by_time(time)

    def is_last_hint(self, hint_number: int) -> bool:
        return len(self.time_hints) == hint_number + 1

    def check(self, action: Action, state: StateHolder) -> Decision:
        decisions = Decisions([cond.check(action, state) for cond in self.conditions])
        implemented = decisions.get_implemented()
        if not implemented:
            return NotImplementedActionDecision()
        if isinstance(action, TypedKeyAction):
            if bonuses := implemented.get_all(BonusKeyDecision):
                return bonuses.get_exactly_one(self.id)
            key_decisions = implemented.get_all(TypedKeyDecision, WrongKeyDecision)
            if not key_decisions:
                return NotImplementedActionDecision()
            if not key_decisions.get_significant():
                assert all(d.type == DecisionType.NO_ACTION for d in key_decisions)
                if duplicate_correct := key_decisions.get_all(TypedKeyDecision):
                    return duplicate_correct.get_exactly_one(self.id)
                return key_decisions[0]
            significant_key_decisions = key_decisions.get_significant()
            return significant_key_decisions.get_exactly_one(self.id)
        else:
            return NotImplementedActionDecision()

    def get_keys(self) -> set[SHKey]:
        return self.conditions.get_keys()

    def get_bonus_keys(self) -> set[BonusKey]:
        return self.conditions.get_bonus_keys()

    def get_guids(self) -> list[str]:
        guids = []
        for hint in self.time_hints:
            guids.extend(hint.get_guids())
        return guids

    @property
    def hints_count(self) -> int:
        return self.time_hints.hints_count + self.conditions.hints_count

    def get_hints_for_timedelta(self, delta: timedelta) -> list[TimeHint]:
        return self.time_hints.get_hints_for_timedelta(delta)

    @classmethod
    def legacy_factory(
        cls,
        id: str,  # noqa: A002
        time_hints: HintsList,
        keys: set[SHKey],
        bonus_keys: set[BonusKey] | None = None,
    ) -> "LevelScenario":
        conditions: list[AnyCondition] = [KeyWinCondition(keys)]
        if bonus_keys:
            conditions.append(KeyBonusCondition(bonus_keys))
        return cls(
            id=id,
            time_hints=time_hints,
            conditions=Conditions(conditions),
            __model_version__=1,
        )

    def is_routed(self) -> bool:
        return bool(self.conditions.get_routed_conditions())


def check_all_files_saved(level: LevelScenario, guids: set[str]):
    for hints_ in level.time_hints:
        check_all_files_in_hints_saved(hints_.hint, guids)
    for condition in level.conditions:
        if isinstance(condition, action.KeyBonusHintCondition):
            check_all_files_in_hints_saved(condition.bonus_hint, guids)


def check_all_files_in_hints_saved(hints_: list[hints.AnyHint], guids: set[str]):
    for hint in hints_:
        if isinstance(hint, hints.FileMixin) and hint.file_guid not in guids:
            raise exceptions.FileNotFound(text=f"not found {hint.file_guid} in files")
