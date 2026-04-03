import uuid
from dataclasses import dataclass, field
from typing import Sequence
from uuid import UUID

from shvatka.core.models.dto import hints


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
            self.bonus_minutes != 0.0
            and not self.hints_
            and not self.level_up
            and self.next_level is None
        )

    def is_routed_level_up(self) -> bool:
        return self.level_up and self.next_level is not None

    @classmethod
    def empty(cls) -> "Effects":
        return cls(id=uuid.uuid4())
