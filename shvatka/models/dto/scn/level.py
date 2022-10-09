import typing
from dataclasses import dataclass, field

from shvatka.models.dto.scn.time_hint import TimeHint

SHKey: typing.TypeAlias = str


@dataclass
class LevelScenario:
    id: str
    time_hints: list[TimeHint]
    keys: set[SHKey] = field(default_factory=set)

    def get_hint(self, hint_number: int) -> TimeHint:
        return self.time_hints[hint_number]

    def is_last_hint(self, hint_number: int) -> bool:
        return len(self.time_hints) == hint_number -1

    def get_keys(self):
        return self.keys
