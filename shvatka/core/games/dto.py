from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints, action


@dataclass(kw_only=True, frozen=True, slots=True)
class Event:
    id: int
    level_time_id: int
    at: datetime
    effects: action.Effects
    key: action.SHKey | None = None
    is_timer: bool


@dataclass(kw_only=True, frozen=True, slots=True)
class CurrentHintsAndKeys:
    hints: list[hints.TimeHint]
    typed_keys: list[dto.InsertedKey]
    events: list[Event]
    level_number: int
    level_time_id: int
    started_at: datetime
    game_id: int
    is_finished: bool
    level_numbers_by_name_id: dict[str, int]
    """Mapping of level name_id to its number_in_game, used to resolve effects' next_level."""


@dataclass(kw_only=True, frozen=True, slots=True)
class CurrentHintsOnly:
    hints: list[hints.TimeHint]
    level_number: int
    level_time_id: int
    started_at: datetime
    game_id: int
    is_finished: bool

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
