from dataclasses import dataclass
from enum import Enum, auto
from typing import Sequence

from shvatka.core.models.dto import hints


class EffectType(Enum):
    level_up = auto()
    bonus_minutes = auto()
    bonus_hint = auto()


@dataclass(kw_only=True)
class Effects:
    hints: Sequence[hints.AnyHint] = tuple()
    bonus_minutes: float = 0.0
    level_up: bool = False
    next_level: str | None = None
