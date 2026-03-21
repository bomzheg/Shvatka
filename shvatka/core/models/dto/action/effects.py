from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Sequence
from uuid import UUID

from shvatka.core.models.dto import hints


class EffectType(Enum):
    level_up = auto()
    bonus_minutes = auto()
    bonus_hint = auto()


@dataclass(kw_only=True)
class Effects:
    id: UUID
    hints_: Sequence[hints.AnyHint] = field(default_factory=tuple)
    bonus_minutes: float = 0.0
    level_up: bool = False
    next_level: str | None = None

    def is_no_effects(self) -> bool:
        return not any((self.next_level, self.level_up, self.bonus_minutes, self.hints_))

    def is_bonus_only(self) -> bool:
        return (
            self.bonus_minutes != 0
            and not self.hints_
            and not self.level_up
            and self.next_level is None
        )
