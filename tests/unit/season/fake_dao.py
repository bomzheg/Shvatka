"""An in-memory `SeasonScheduleDao`, so the interactors are testable without a db.

It keeps the little the interactors actually depend on: dates in a list, the
change rows they append, and the notifications they ask for. Everything else —
ordering, locking, the announcer — is the interactor's own decision, which is
exactly what these tests are about.
"""

from collections.abc import Collection, Sequence
from datetime import date, datetime
from typing import Any

from shvatka.core.models import dto
from shvatka.core.models.enums.notification import NotificationSeverity, NotificationType
from shvatka.core.notifications import dto as notification_dto
from shvatka.core.season import dto as season_dto
from shvatka.core.season.adapters import SeasonScheduleDao
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc

NOW = datetime(2026, 8, 1, 10, tzinfo=tz_utc)


class SentNotification:
    def __init__(
        self,
        recipient_ids: Collection[int],
        type_: NotificationType,
        severity: NotificationSeverity,
        payload: dict[str, Any],
    ) -> None:
        self.recipient_ids = set(recipient_ids)
        self.type = type_
        self.severity = severity
        self.payload = payload


class FakeSeasonDao(SeasonScheduleDao):
    def __init__(
        self,
        *,
        players: Sequence[dto.Player] = (),
        teams: Sequence[dto.Team] = (),
        games: Sequence[dto.Game] = (),
        recipients: Collection[int] = (),
        now: datetime = NOW,
    ) -> None:
        self.seasons: dict[int, season_dto.Season] = {}
        self.slots: list[season_dto.Slot] = []
        self.changes: list[season_dto.ScheduleChange] = []
        self.notifications: list[SentNotification] = []
        self.players = {player.id: player for player in players}
        self.teams = {team.id: team for team in teams}
        self.games = {game.id: game for game in games}
        self.recipients = set(recipients)
        self.now = now
        self.commits = 0
        self.locked: list[int] = []
        self._next_id = 1

    # -- reads ---------------------------------------------------------------

    def _slots_of(self, season_id: int) -> list[season_dto.Slot]:
        return sorted(
            (slot for slot in self.slots if slot.season_id == season_id),
            key=lambda slot: slot.date,
        )

    async def get_season(self, year: int) -> season_dto.Season | None:
        season = self.seasons.get(year)
        if season is None:
            return None
        season.slots = self._slots_of(season.id)
        return season

    async def get_season_by_id(self, season_id: int) -> season_dto.Season | None:
        for season in self.seasons.values():
            if season.id == season_id:
                season.slots = self._slots_of(season.id)
                return season
        return None

    async def get_season_years(self) -> Sequence[int]:
        return sorted(self.seasons, reverse=True)

    async def get_seasons_to_close(self, today: date) -> Sequence[season_dto.Season]:
        closable = []
        for season in self.seasons.values():
            season.slots = self._slots_of(season.id)
            last = season.last_date
            if season.unpinned_at is None and season.is_announced and last and last < today:
                closable.append(season)
        return closable

    async def get_slot(self, slot_id: int) -> season_dto.Slot:
        for slot in self.slots:
            if slot.id == slot_id:
                return slot
        raise exceptions.SlotNotFound(text=f"no slot {slot_id}")

    async def get_slot_by_game(self, game_id: int) -> season_dto.Slot | None:
        return next(
            (slot for slot in self.slots if slot.game is not None and slot.game.id == game_id),
            None,
        )

    async def lock_slot(self, slot_id: int) -> season_dto.Slot:
        self.locked.append(slot_id)
        return await self.get_slot(slot_id)

    # -- writes --------------------------------------------------------------

    def _take_id(self) -> int:
        self._next_id += 1
        return self._next_id

    async def create_season(self, year: int, published_by_id: int) -> season_dto.Season:
        season = season_dto.Season(
            id=self._take_id(),
            year=year,
            published_by_id=published_by_id,
            published_at=self.now,
            updated_at=self.now,
        )
        self.seasons[year] = season
        return season

    async def set_announcement(self, season_id: int, *, chat_id: int, message_id: int) -> None:
        season = await self.get_season_by_id(season_id)
        assert season is not None
        season.log_chat_id = chat_id
        season.log_message_id = message_id

    async def set_unpinned(self, season_id: int) -> None:
        season = await self.get_season_by_id(season_id)
        assert season is not None
        season.unpinned_at = self.now

    async def touch_season(self, season_id: int) -> None:
        season = await self.get_season_by_id(season_id)
        assert season is not None
        season.updated_at = self.now

    async def add_slot(
        self, season_id: int, day: date, note: str | None = None
    ) -> season_dto.Slot:
        slot = season_dto.Slot(id=self._take_id(), season_id=season_id, date=day, note=note)
        self.slots.append(slot)
        return slot

    async def move_slot(self, slot_id: int, day: date) -> None:
        (await self.get_slot(slot_id)).date = day

    async def set_slot_note(self, slot_id: int, note: str | None) -> None:
        (await self.get_slot(slot_id)).note = note

    async def remove_slot(self, slot_id: int) -> None:
        slot = await self.get_slot(slot_id)
        self.slots.remove(slot)
        # the fk is ON DELETE SET NULL: the change rows outlive the date
        for change in self.changes:
            if change.slot_id == slot_id:
                change.slot_id = None

    async def take_slot(
        self,
        slot_id: int,
        *,
        owner_id: int,
        author_kind: season_dto.SlotAuthorKind,
        team_id: int | None = None,
    ) -> None:
        slot = await self.get_slot(slot_id)
        slot.owner = self.players[owner_id]
        slot.author_kind = author_kind
        slot.team = self.teams[team_id] if team_id is not None else None
        slot.taken_at = self.now

    async def release_slot(self, slot_id: int) -> None:
        slot = await self.get_slot(slot_id)
        slot.owner = None
        slot.author_kind = None
        slot.team = None
        slot.taken_at = None

    async def link_game(self, slot_id: int, game_id: int) -> None:
        game = self.games[game_id]
        (await self.get_slot(slot_id)).game = season_dto.LinkedGame(
            id=game.id, name=game.name, start_at=game.start_at, number=game.number
        )

    async def unlink_game(self, slot_id: int) -> None:
        (await self.get_slot(slot_id)).game = None

    async def set_slot_orgs(self, slot_id: int, player_ids: Collection[int]) -> None:
        (await self.get_slot(slot_id)).orgs = [self.players[id_] for id_ in player_ids]

    # -- the change trail ----------------------------------------------------

    async def add_change(
        self,
        *,
        season_id: int,
        type_: season_dto.ChangeType,
        slot_id: int | None = None,
        actor_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> season_dto.ScheduleChange:
        change = season_dto.ScheduleChange(
            id=self._take_id(),
            season_id=season_id,
            type=type_,
            created_at=self.now,
            slot_id=slot_id,
            actor_id=actor_id,
            payload=payload or {},
        )
        self.changes.append(change)
        return change

    async def mark_changes_published(self, change_ids: Collection[int]) -> None:
        for change in self.changes:
            if change.id in change_ids and change.published_at is None:
                change.published_at = self.now

    async def get_unpublished_changes(self, season_id: int) -> Sequence[season_dto.ScheduleChange]:
        return [
            change
            for change in self.changes
            if change.season_id == season_id and change.published_at is None
        ]

    async def get_season_ids_with_unpublished_changes(self) -> Sequence[int]:
        return sorted({change.season_id for change in self.changes if change.published_at is None})

    # -- everything else -----------------------------------------------------

    async def get_recipient_ids(self, since: datetime) -> set[int]:
        self.audience_since = since
        return set(self.recipients)

    async def get_player_by_id(self, id_: int) -> dto.Player:
        return self.players[id_]

    async def get_team_by_id(self, id_: int) -> dto.Team:
        return self.teams[id_]

    async def get_game_by_id(self, id_: int) -> dto.Game:
        return self.games[id_]

    async def create(
        self,
        *,
        recipient_id: int,
        type_: NotificationType,
        severity: NotificationSeverity = NotificationSeverity.normal,
        actor_id: int | None = None,
        payload: dict[str, Any] | None = None,
        request_id: int | None = None,
    ) -> notification_dto.Notification:
        raise NotImplementedError("season notifications always go to many recipients")

    async def create_for_recipients(
        self,
        *,
        recipient_ids: Collection[int],
        type_: NotificationType,
        severity: NotificationSeverity = NotificationSeverity.normal,
        actor_id: int | None = None,
        payload: dict[str, Any] | None = None,
        request_id: int | None = None,
    ) -> None:
        self.notifications.append(SentNotification(recipient_ids, type_, severity, payload or {}))

    async def commit(self) -> None:
        self.commits += 1
