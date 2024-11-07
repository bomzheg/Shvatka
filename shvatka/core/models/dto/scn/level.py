import logging
from collections.abc import Sequence, Iterable
from dataclasses import dataclass
from datetime import timedelta
from typing import overload

from shvatka.common.log_utils import obfuscate_sensitive
from shvatka.core.utils import exceptions
from .hint_part import AnyHint
from .time_hint import TimeHint, EnumeratedTimeHint
from shvatka.core.models.dto.action import (
    WinCondition,
    Action,
    Decision,
    StateHolder,
    DecisionType,
    Decisions,
    KeyDecision,
    KeyBonusCondition,
    NotImplementedActionDecision,
)
from shvatka.core.models.dto.action.keys import (
    SHKey,
    KeyWinCondition,
    TypedKeyAction,
    WrongKeyDecision,
    BonusKey,
)

logger = logging.getLogger(__name__)


class HintsList(Sequence[TimeHint]):
    def __init__(self, hints: list[TimeHint]):
        self.verify(hints)
        self.hints = hints

    @classmethod
    def parse(cls, hints: list[TimeHint]):
        return cls(cls.normalize(hints))

    @staticmethod
    def normalize(hints: list[TimeHint]) -> list[TimeHint]:
        hint_map: dict[int, list[AnyHint]] = {}
        for hint in hints:
            if not hint.hint:
                continue
            hint_map.setdefault(hint.time, []).extend(hint.hint)
        return [TimeHint(k, v) for k, v in sorted(hint_map.items(), key=lambda x: x[0])]

    @staticmethod
    def verify(hints: Iterable[TimeHint]) -> None:
        current_time = -1
        times: set[int] = set()
        for hint in hints:
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


class Conditions(Sequence[WinCondition]):
    def __init__(self, conditions: Sequence[WinCondition]):
        self.validate(conditions)
        self.conditions = conditions

    @staticmethod
    def validate(conditions: Sequence[WinCondition]) -> None:
        keys: set[str] = set()
        win_conditions = []
        for c in conditions:
            if isinstance(c, KeyWinCondition):
                win_conditions.append(c)
                if keys.intersection(c.keys):
                    raise exceptions.LevelError(
                        text=f"keys already exists {keys.intersection(c.keys)}"
                    )
                keys = keys.union(c.keys)
            elif isinstance(c, KeyBonusCondition):
                if keys.intersection({k.text for k in c.keys}):
                    raise exceptions.LevelError(
                        text=f"keys already exists {keys.intersection(c.keys)}"
                    )
                keys = keys.union({k.text for k in c.keys})
        if not win_conditions:
            raise exceptions.LevelError(text="There is no win condition")

    def get_keys(self) -> set[str]:
        result: set[SHKey] = set()
        for condition in self.conditions:
            if isinstance(condition, KeyWinCondition):
                result = result.union(condition.keys)
        return result

    def get_bonus_keys(self) -> set[BonusKey]:
        result: set[BonusKey] = set()
        for condition in self.conditions:
            if isinstance(condition, KeyBonusCondition):
                result = result.union(condition.keys)
        return result

    @overload
    def __getitem__(self, index: int) -> WinCondition:
        return self.conditions[index]

    @overload
    def __getitem__(self, index: slice) -> Sequence[WinCondition]:
        return self.conditions[index]

    def __getitem__(self, index):
        return self.conditions[index]

    def __len__(self):
        return len(self.conditions)

    def __repr__(self):
        return repr(self.conditions)


@dataclass
class LevelScenario:
    id: str
    time_hints: HintsList
    conditions: Conditions

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
            key_decisions = implemented.get_all(KeyDecision, WrongKeyDecision)
            if not key_decisions:
                return NotImplementedActionDecision()
            if not key_decisions.get_significant():
                assert all(d.type == DecisionType.NO_ACTION for d in key_decisions)
                if duplicate_correct := key_decisions.get_all(KeyDecision):
                    if len(duplicate_correct) != 1:
                        logger.warning(
                            "more than one duplicate correct key decision %s",
                            obfuscate_sensitive(duplicate_correct),
                        )
                    return duplicate_correct[0]
                return key_decisions[0]
            significant_key_decisions = key_decisions.get_significant()
            if len(significant_key_decisions) != 1:
                logger.warning(
                    "More than one significant key decision. "
                    "Will used first but it's not clear %s",
                    obfuscate_sensitive(significant_key_decisions),
                )
            return significant_key_decisions[0]
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
        return self.time_hints.hints_count

    def get_hints_for_timedelta(self, delta: timedelta) -> list[TimeHint]:
        return self.time_hints.get_hints_for_timedelta(delta)
