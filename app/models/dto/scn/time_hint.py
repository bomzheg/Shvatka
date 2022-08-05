from dataclasses import dataclass

from app.models.dto.scn.hint_part import AnyHint


@dataclass
class TimeHint:
    time: int
    hint: list[AnyHint]
