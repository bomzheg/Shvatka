from dataclasses import dataclass

from app.models.dto.scn.hint_part import BaseHint


@dataclass
class TimeHint:
    time: int
    hint: list[BaseHint]
