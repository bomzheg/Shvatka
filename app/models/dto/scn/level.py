import typing
from dataclasses import dataclass, field

from app.models.dto.scn.time_hint import TimeHint

SHKey: typing.TypeAlias = str


@dataclass
class LeveScenario:
    id: str
    time_hints: list[TimeHint]
    keys: set[SHKey] = field(default_factory=set)
