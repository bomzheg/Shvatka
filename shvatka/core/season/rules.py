"""Pure season rules: the default calendar, permissions, the near search, collapsing.

Nothing here touches a dao, a clock or a view — every function takes what it
needs and returns a value, so all of it is unit-testable without a database.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from shvatka.core.models import dto
from shvatka.core.players.player import check_allow_be_author, is_team_captain
from shvatka.core.season import dto as season_dto
from shvatka.core.utils import exceptions

SEASON_SLOTS_COUNT = 9
SEASON_SLOT_INTERVAL = timedelta(days=21)
SEASON_START_AFTER = (5, 9)  # 9 May
SATURDAY = 5  # date.weekday() numbers Monday 0
SLOT_SUGGEST_WINDOW = timedelta(days=3)


def default_slot_dates(year: int) -> list[date]:
    """The plan every season starts from: nine dates, every three weeks."""
    first = first_saturday_after(date(year, *SEASON_START_AFTER))
    return [first + SEASON_SLOT_INTERVAL * i for i in range(SEASON_SLOTS_COUNT)]


def first_saturday_after(day: date) -> date:
    # strictly after: a Saturday falling exactly on 9 May is skipped
    delta = (SATURDAY - day.weekday()) % 7
    return day + timedelta(days=delta or 7)


def check_can_add_slot(player: dto.Player) -> None:
    """Adding a date to a published season is open to any author."""
    check_allow_be_author(player)


def check_can_edit_slot(
    slot: season_dto.Slot, player: dto.Player, *, is_superuser: bool = False
) -> None:
    """Moving, renaming or deleting a date. A taken date is locked to its owner."""
    check_allow_be_author(player)
    if is_superuser or slot.is_free or slot.is_mine(player):
        return
    raise exceptions.NotSlotOwner(
        player=player,
        text=f"slot {slot.id} at {slot.date.isoformat()} belongs to someone else",
    )


def check_can_take_slot(
    slot: season_dto.Slot,
    player: dto.Player,
    *,
    author_kind: season_dto.SlotAuthorKind,
    team: dto.Team | None,
    is_superuser: bool = False,
) -> None:
    """Taking a free date, or re-taking your own to change its author or orgs."""
    check_allow_be_author(player)
    if not (is_superuser or slot.is_free or slot.is_mine(player)):
        raise exceptions.SlotAlreadyTaken(
            player=player,
            text=f"slot {slot.id} at {slot.date.isoformat()} is already taken",
        )
    if author_kind == season_dto.SlotAuthorKind.team:
        if team is None:
            raise exceptions.SlotAuthorInvalid(
                player=player, text="a team author needs a team to author the game"
            )
        if not (is_superuser or is_team_captain(team, player)):
            raise exceptions.SlotAuthorInvalid(
                player=player,
                team=team,
                text="only the captain may sign their team up for a date",
            )


def find_slots_near(
    slots: Iterable[season_dto.Slot],
    at: date,
    player: dto.Player | None = None,
    window: timedelta = SLOT_SUGGEST_WINDOW,
) -> list[season_dto.Slot]:
    """Dates the engine may offer for a game starting on `at`, nearest first.

    Only dates that are free or already the player's own — offering someone
    else's date would be an offer the engine has to refuse afterwards.
    """
    candidates = [
        slot
        for slot in slots
        if abs((slot.date - at).days) <= window.days
        and (slot.is_free or slot.is_mine(player))
        and not slot.is_linked
    ]
    # a tie (one date before, one after, equally far) resolves to the earlier one
    return sorted(candidates, key=lambda slot: (abs((slot.date - at).days), slot.date))


@dataclass
class SlotDigest:
    """The net effect of every change to one date since the last digest."""

    day: date | None = None
    """Where the date stands after every change in the window."""
    added: bool = False
    removed: bool = False
    date_before: date | None = None
    date_after: date | None = None
    note: str | None = None
    note_changed: bool = False
    owner: str | None = None
    released: bool = False
    orgs: list[str] = field(default_factory=list)
    orgs_changed: bool = False
    game: str | None = None
    game_unlinked: bool = False
    by_superuser: bool = False

    @property
    def moved(self) -> bool:
        return (
            self.date_before is not None
            and self.date_after is not None
            and self.date_before != self.date_after
        )

    @property
    def is_empty(self) -> bool:
        if self.added or self.removed:
            return False
        return not (
            self.moved
            or self.note_changed
            or self.orgs_changed
            or self.released
            or self.owner is not None
            or self.game is not None
            or self.game_unlinked
        )


def collapse_changes(changes: Sequence[season_dto.ScheduleChange]) -> list[SlotDigest]:
    """Five edits of one date become one line; an edit and its undo become none.

    Rows are grouped by the date they belong to. A removed date takes its
    `slot_id` with it (the fk is `ON DELETE SET NULL`), so orphaned rows fall
    back to the date their payload denormalized — which is why every payload
    carries one.
    """
    digests: dict[object, SlotDigest] = {}
    for change in sorted(changes, key=lambda c: (c.created_at, c.id)):
        digest = digests.setdefault(_group_key(change), SlotDigest())
        _apply(digest, change)
    return sorted(
        (digest for digest in digests.values() if not digest.is_empty),
        key=lambda digest: (digest.day or date.max, digest.added, digest.removed),
    )


def _group_key(change: season_dto.ScheduleChange) -> object:
    if change.slot_id is not None:
        return change.slot_id
    # the date is gone: everything the payload said about it is all there is
    return ("date", change.payload.get("date") or change.payload.get("from"))


def _apply(digest: SlotDigest, change: season_dto.ScheduleChange) -> None:
    payload = change.payload
    digest.by_superuser = digest.by_superuser or change.by_superuser
    match change.type:
        case season_dto.ChangeType.slot_added:
            digest.added = True
            digest.day = _payload_date(payload, "date") or digest.day
        case season_dto.ChangeType.slot_removed:
            if digest.added:
                # added and removed before anyone was told: it never happened
                _reset_digest(digest)
                digest.removed = False
                digest.added = False
                return
            digest.removed = True
            digest.day = _payload_date(payload, "date") or digest.day
        case season_dto.ChangeType.slot_moved:
            if digest.date_before is None:
                digest.date_before = _payload_date(payload, "from")
            digest.date_after = _payload_date(payload, "to")
            digest.day = digest.date_after or digest.day
        case season_dto.ChangeType.slot_taken:
            digest.owner = payload.get("author")
            digest.released = False
            digest.day = _payload_date(payload, "date") or digest.day
        case season_dto.ChangeType.slot_released:
            if digest.owner is not None:
                # taken and given back within the day: nothing net changed
                digest.owner = None
            else:
                digest.released = True
            digest.day = _payload_date(payload, "date") or digest.day
        case season_dto.ChangeType.slot_orgs_changed:
            digest.orgs = list(payload.get("orgs") or [])
            digest.orgs_changed = True
            digest.day = _payload_date(payload, "date") or digest.day
        case season_dto.ChangeType.slot_note_changed:
            digest.note = payload.get("note")
            digest.note_changed = True
            digest.day = _payload_date(payload, "date") or digest.day
        case season_dto.ChangeType.slot_game_linked:
            digest.game = payload.get("game")
            digest.game_unlinked = False
            digest.day = _payload_date(payload, "date") or digest.day
        case season_dto.ChangeType.slot_game_unlinked:
            if digest.game is not None:
                digest.game = None
            else:
                digest.game_unlinked = True
            digest.day = _payload_date(payload, "date") or digest.day


def _reset_digest(digest: SlotDigest) -> None:
    """Forget everything said about a date that no longer exists."""
    digest.date_before = None
    digest.date_after = None
    digest.owner = None
    digest.released = False
    digest.orgs = []
    digest.orgs_changed = False
    digest.note = None
    digest.note_changed = False
    digest.game = None
    digest.game_unlinked = False


def _payload_date(payload: dict, key: str) -> date | None:
    raw = payload.get(key)
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None
