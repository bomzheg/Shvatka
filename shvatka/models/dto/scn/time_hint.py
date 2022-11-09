from dataclasses import dataclass

from .hint_part import AnyHint


@dataclass
class TimeHint:
    time: int
    hint: list[AnyHint]

    def get_guids(self) -> list[str]:
        guids = []
        for hint in self.hint:
            guids.extend(hint.get_guids())
        return guids
