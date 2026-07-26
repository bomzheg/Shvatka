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
    """Что именно принесло команде бонус (или штраф)."""

    key = enum.auto()
    timer = enum.auto()
    unknown = enum.auto()


@dataclass(kw_only=True, frozen=True, slots=True)
class BonusEvent:
    """Одно событие, изменившее время команды: бонус (>0) или штраф (<0).

    ``level_time_id`` в БД nullable, поэтому уровень может остаться нерешённым —
    тогда ``level_number`` равен None и бонус учитывается только в итоге.
    """

    at: datetime
    minutes: float
    source: BonusSource
    key: action.SHKey | None
    level_time_id: int | None
    level_number: int | None = None

    def with_level_number(self, level_number: int | None) -> "BonusEvent":
        return BonusEvent(
            at=self.at,
            minutes=self.minutes,
            source=self.source,
            key=self.key,
            level_time_id=self.level_time_id,
            level_number=level_number,
        )

    @property
    def td(self) -> timedelta:
        """Сколько времени бонус снимает с результата (штраф — отрицательный)."""
        return timedelta(minutes=self.minutes)


@dataclass(kw_only=True, frozen=True, slots=True)
class GameStatWithBonuses:
    """Статистика игры вместе с бонусами и штрафами команд.

    Скорректированные времена здесь не считаются: отдаём исходные времена и
    сами бонусы, чтобы клиент мог переключать режимы отображения без запросов.
    """

    level_times: dict[dto.Team, list[dto.LevelTimeOnGame]]
    bonuses: dict[int, list[BonusEvent]]
    """{team_id: [...]} — только команды, у которых бонусы есть."""


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
