import typing
from dataclasses import dataclass, field
from datetime import timedelta

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


@dataclass
class LevelScenario:
    id: str
    time_hints: list[TimeHint]
    keys: set[SHKey] = field(default_factory=set)
    bonus_keys: set[BonusKey] = field(default_factory=set)

    def get_hint(self, hint_number: int) -> TimeHint:
        return self.time_hints[hint_number]

    def get_hint_by_time(self, time: timedelta) -> EnumeratedTimeHint:
        hint = self.time_hints[0]
        number = 0
        for i, h in enumerate(self.time_hints):
            if timedelta(minutes=h.time) < time:
                hint = h
                number = i
            else:
                break
        return EnumeratedTimeHint(time=hint.time, hint=hint.hint, number=number)

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
        return sum(time_hint.hints_count for time_hint in self.time_hints)

    def get_hints_for_timedelta(self, delta: timedelta) -> list[TimeHint]:
        minutes = delta.total_seconds() // 60
        return [th for th in self.time_hints if th.time <= minutes]
