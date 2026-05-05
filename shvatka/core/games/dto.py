from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints


@dataclass(kw_only=True, frozen=True, slots=True)
class CurrentHintsAndKeys:
    hints: list[hints.TimeHint]
    typed_keys: list[dto.KeyTime]
    events: list[dto.GameEvent]
    level_number: int
    level_time_id: int
    started_at: datetime
    game_id: int


@dataclass(kw_only=True, frozen=True, slots=True)
class CurrentHintsOnly:
    hints: list[hints.TimeHint]
    level_number: int
    level_time_id: int
    started_at: datetime
    game_id: int

    def get_guids(self) -> list[str]:
        return [g for h in self.hints for g in h.get_guids()]


@dataclass(kw_only=True, frozen=True, slots=True)
class FoundBonusHints:
    bonus_hints: dict[UUID, list[hints.AnyHint]]
    """{effect_id: []}"""


@dataclass(kw_only=True, frozen=True, slots=True)
class MyRole:
    waiver_vote: enums.Played | None
    team: dto.Team | None
    org: dto.Organizer | None
