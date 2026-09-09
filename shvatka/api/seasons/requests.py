from collections.abc import Sequence
from dataclasses import dataclass, field

# a field named `date` shadows the type in the class namespace, and pydantic
# evaluates the annotations there — so the type travels under its own name
from datetime import date as date_

from shvatka.core.season import dto


@dataclass
class SlotDraft:
    date: date_
    note: str | None = None

    def to_core(self) -> dto.SlotDraft:
        return dto.SlotDraft(date=self.date, note=self.note)


@dataclass
class PublishSeason:
    year: int
    slots: Sequence[SlotDraft] = field(default_factory=list)


@dataclass
class AddSlot:
    date: date_
    note: str | None = None


@dataclass
class EditSlot:
    date: date_ | None = None
    note: str | None = None
    """Omitted leaves the note alone; an empty string clears it."""


@dataclass
class TakeSlot:
    author_kind: str = dto.SlotAuthorKind.player.name
    team_id: int | None = None
    org_player_ids: Sequence[int] = field(default_factory=list)

    def kind(self) -> dto.SlotAuthorKind:
        return dto.SlotAuthorKind[self.author_kind]


@dataclass
class SetSlotOrgs:
    org_player_ids: Sequence[int] = field(default_factory=list)


@dataclass
class LinkGame:
    game_id: int
