from collections.abc import Sequence
from dataclasses import dataclass

# see requests.py: a field named `date` would shadow the type here too
from datetime import date as date_
from datetime import datetime
from typing import Self

from shvatka.api.shared.responses import Player, Team
from shvatka.core.season import dto


@dataclass
class LinkedGame:
    id: int
    name: str
    start_at: datetime | None
    number: int | None

    @classmethod
    def from_core(cls, core: dto.LinkedGame) -> Self:
        return cls(id=core.id, name=core.name, start_at=core.start_at, number=core.number)


@dataclass
class Slot:
    id: int
    date: date_
    note: str | None
    owner: Player | None
    author_kind: str | None
    team: Team | None
    orgs: Sequence[Player]
    game: LinkedGame | None
    taken_at: datetime | None
    is_free: bool

    @classmethod
    def from_core(cls, core: dto.Slot) -> Self:
        return cls(
            id=core.id,
            date=core.date,
            note=core.note,
            owner=Player.from_core(core.owner) if core.owner else None,
            author_kind=core.author_kind.name if core.author_kind else None,
            team=Team.from_core(core.team),
            orgs=[Player.from_core(org) for org in core.orgs],
            game=LinkedGame.from_core(core.game) if core.game else None,
            taken_at=core.taken_at,
            is_free=core.is_free,
        )


@dataclass
class Season:
    id: int
    year: int
    published_at: datetime
    updated_at: datetime
    slots: Sequence[Slot]

    @classmethod
    def from_core(cls, core: dto.Season) -> Self:
        return cls(
            id=core.id,
            year=core.year,
            published_at=core.published_at,
            updated_at=core.updated_at,
            slots=[Slot.from_core(slot) for slot in core.slots],
        )


@dataclass
class SeasonYears:
    years: Sequence[int]


@dataclass
class DefaultSlotDates:
    year: int
    dates: Sequence[date_]
