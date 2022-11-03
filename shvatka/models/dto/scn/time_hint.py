from dataclasses import dataclass

from .hint_part import AnyHint


@dataclass
class TimeHint:
    time: int
    hint: list[AnyHint]
