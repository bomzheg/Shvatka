import typing
from collections.abc import Sequence, Iterable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import overload


from shvatka.core.utils import exceptions
from .hint_part import AnyHint
from .time_hint import TimeHint, EnumeratedTimeHint

SHKey: typing.TypeAlias = str


@dataclass(frozen=True)
class BonusKey:
    text: str
    bonus_minutes: float

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BonusKey):
            return NotImplemented
        return self.text == other.text

    def __hash__(self) -> int:
        return hash(self.text)


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
        times: set[int] = set()
        for hint in hints:
            if hint.time in times:
                raise exceptions.LevelError(
                    text=f"Contains multiple times hints for time {hint.time}"
                )
            times.add(hint.time)
            if not hint.hint:
                raise exceptions.LevelError(text=f"There is no hint for time {hint.time}")

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
        result = self.hints[0:old_index] + self.hints[old_index + 1 :] + [new]
        return self.__class__(self.normalize(result))

    @property
    def hints_count(self) -> int:
        return sum(time_hint.hints_count for time_hint in self.hints)

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


@dataclass
class LevelScenario:
    id: str
    time_hints: HintsList
    keys: set[SHKey] = field(default_factory=set)
    bonus_keys: set[BonusKey] = field(default_factory=set)

    def get_hint(self, hint_number: int) -> TimeHint:
        return self.time_hints[hint_number]

    def get_hint_by_time(self, time: timedelta) -> EnumeratedTimeHint:
        return self.time_hints.get_hint_by_time(time)

    def is_last_hint(self, hint_number: int) -> bool:
        return len(self.time_hints) == hint_number + 1

    def get_keys(self) -> set[str]:
        return self.keys

    def get_bonus_keys(self) -> set[BonusKey]:
        return self.bonus_keys

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
