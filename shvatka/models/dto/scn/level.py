import typing
from dataclasses import dataclass, field

from .time_hint import TimeHint

SHKey: typing.TypeAlias = str


@dataclass
class LevelScenario:
    id: str
    time_hints: list[TimeHint]
    keys: set[SHKey] = field(default_factory=set)

    def get_hint(self, hint_number: int) -> TimeHint:
        return self.time_hints[hint_number]

    def is_last_hint(self, hint_number: int) -> bool:
        return len(self.time_hints) == hint_number + 1

    def get_keys(self):
        return self.keys

    def get_guids(self) -> list[str]:
        guids = []
        for hint in self.time_hints:
            guids.extend(hint.get_guids())
        return guids

    @property
    def hints_count(self) -> int:
        return sum((time_hint.hints_count for time_hint in self.time_hints))
