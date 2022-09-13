import typing
from dataclasses import dataclass, field

from shvatka.models.dto.scn.time_hint import TimeHint

SHKey: typing.TypeAlias = str


@dataclass
class LevelScenario:
    id: str
    time_hints: list[TimeHint]
    keys: set[SHKey] = field(default_factory=set)
