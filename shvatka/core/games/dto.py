from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from shvatka.core.models import dto
from shvatka.core.models.dto import hints


@dataclass(kw_only=True, frozen=True, slots=True)
class CurrentHintsAndKeys:
    hints: list[hints.TimeHint]
    typed_keys: list[dto.KeyTime]
    level_number: int
    started_at: datetime
    game_id: int


@dataclass(kw_only=True, frozen=True, slots=True)
class CurrentHintsOnly:
    hints: list[hints.TimeHint]
    level_number: int
    started_at: datetime
    game_id: int


@dataclass(kw_only=True, frozen=True, slots=True)
class FoundBonusHints:
    bonus_hints: dict[UUID, list[hints.AnyHint]]
    """{effect_id: []}"""
