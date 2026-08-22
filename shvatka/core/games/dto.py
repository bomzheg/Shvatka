import enum
from dataclasses import dataclass
from datetime import datetime, timedelta
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


class BonusSource(enum.StrEnum):
    """What brought the team a bonus (or a penalty)."""

    key = enum.auto()
    timer = enum.auto()
    unknown = enum.auto()


@dataclass(kw_only=True, frozen=True, slots=True)
class BonusEvent:
    """An event that changed a team's time: bonus (>0 minutes) or penalty (<0).

    Carries the whole ``effects`` rather than just its bonus minutes, so new
    kinds of effect become visible to clients without an API change.

    ``level_time_id`` is nullable in the DB, so the level may stay unresolved —
    then ``level_number`` is None and the bonus only counts towards the total.
    """

    at: datetime
    effects: action.Effects
    source: BonusSource
    key: action.SHKey | None
    level_time_id: int | None
    level_number: int | None = None

    def with_level_number(self, level_number: int | None) -> "BonusEvent":
        return BonusEvent(
            at=self.at,
            effects=self.effects,
            source=self.source,
            key=self.key,
            level_time_id=self.level_time_id,
            level_number=level_number,
        )

    @property
    def minutes(self) -> float:
        return self.effects.bonus_minutes

    @property
    def td(self) -> timedelta:
        """How much time the bonus takes off the result (a penalty is negative)."""
        return timedelta(minutes=self.minutes)


@dataclass(kw_only=True, frozen=True, slots=True)
class GameStatWithBonuses:
    """Game stat together with the teams' bonuses and penalties.

    Adjusted times are not computed here: we hand out the raw times and the
    bonuses themselves, so a client can switch display modes without requests.
    """

    level_times: dict[dto.Team, list[dto.LevelTimeOnGame]]
    bonuses: dict[int, list[BonusEvent]]
    """{team_id: [...]} — only teams that actually have bonuses."""


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
class PassedLevelHints:
    """Hints a team had on a level it has already left.

    Only the hints that were actually published to the team are listed: the
    ones whose time had come between ``started_at`` and ``finished_at``. A team
    that solved a level fast never saw its later hints, and doesn't see them
    here either.
    """

    level_number: int
    level_time_id: int
    started_at: datetime
    finished_at: datetime
    hints: list[hints.TimeHint]

    @property
    def duration(self) -> timedelta:
        return self.finished_at - self.started_at

    def get_guids(self) -> list[str]:
        return [g for h in self.hints for g in h.get_guids()]


@dataclass(kw_only=True, frozen=True, slots=True)
class PassedLevels:
    """Every level the team has left behind, oldest first."""

    game_id: int
    levels: list[PassedLevelHints]

    def get_guids(self) -> list[str]:
        return [g for level in self.levels for g in level.get_guids()]


@dataclass(kw_only=True, frozen=True, slots=True)
class FoundBonusHints:
    bonus_hints: dict[UUID, list[hints.AnyHint]]
    """{effect_id: []}"""


@dataclass(kw_only=True, frozen=True, slots=True)
class MyRole:
    waiver_vote: enums.Played | None
    team: dto.Team | None
    org: dto.Organizer | None
