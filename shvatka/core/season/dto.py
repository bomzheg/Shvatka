from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from shvatka.core.models import dto


class SlotAuthorKind(enum.Enum):
    """Who is going to author the game on a taken date."""

    player = enum.auto()
    team = enum.auto()


class ChangeType(enum.Enum):
    slot_added = enum.auto()
    slot_moved = enum.auto()
    slot_removed = enum.auto()
    slot_taken = enum.auto()
    slot_released = enum.auto()
    slot_orgs_changed = enum.auto()
    slot_note_changed = enum.auto()
    slot_game_linked = enum.auto()
    slot_game_unlinked = enum.auto()


@dataclass(frozen=True)
class LinkedGame:
    """The little a date needs to know about the game sitting in it."""

    id: int
    name: str
    start_at: datetime | None
    number: int | None


@dataclass(frozen=True)
class SlotDraft:
    """One date of a season being composed. Nothing of it is persisted yet."""

    date: date
    note: str | None = None


@dataclass
class Slot:
    id: int
    season_id: int
    date: date
    note: str | None = None
    owner: dto.Player | None = None
    author_kind: SlotAuthorKind | None = None
    team: dto.Team | None = None
    orgs: Sequence[dto.Player] = field(default_factory=list)
    game: LinkedGame | None = None
    taken_at: datetime | None = None

    @property
    def is_free(self) -> bool:
        return self.owner is None

    @property
    def is_linked(self) -> bool:
        return self.game is not None

    def is_mine(self, player: dto.Player | None) -> bool:
        return player is not None and self.owner is not None and self.owner.id == player.id

    @property
    def author_name(self) -> str | None:
        if self.author_kind == SlotAuthorKind.team and self.team is not None:
            return self.team.name
        if self.owner is not None:
            return self.owner.name_mention
        return None


@dataclass
class Season:
    id: int
    year: int
    published_by_id: int
    published_at: datetime
    updated_at: datetime
    slots: Sequence[Slot] = field(default_factory=list)
    log_chat_id: int | None = None
    log_message_id: int | None = None
    unpinned_at: datetime | None = None

    @property
    def is_announced(self) -> bool:
        return self.log_chat_id is not None and self.log_message_id is not None

    @property
    def last_date(self) -> date | None:
        return max((slot.date for slot in self.slots), default=None)


@dataclass
class ScheduleChange:
    id: int
    season_id: int
    type: ChangeType
    created_at: datetime
    slot_id: int | None = None
    actor_id: int | None = None
    by_superuser: bool = False
    payload: dict[str, Any] = field(default_factory=dict)
    published_at: datetime | None = None
