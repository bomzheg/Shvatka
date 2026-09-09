from __future__ import annotations

import logging
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums.notification import NotificationSeverity, NotificationType
from shvatka.core.season import dto as season_dto
from shvatka.core.season.adapters import SeasonScheduleDao
from shvatka.core.season.rules import (
    SLOT_SUGGEST_WINDOW,
    SlotDigest,
    check_can_edit_schedule,
    check_can_take_slot,
    collapse_changes,
    default_slot_dates,
    find_slots_near,
)
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.core.views.season import SeasonAnnouncer

logger = logging.getLogger(__name__)

AUDIENCE_YEARS_BACK = 1
"""The digest reaches everyone active this year or the previous one."""


class GetDefaultSlotDatesInteractor:
    """The nine dates a season is composed from. Reads nothing, writes nothing."""

    async def __call__(self, year: int) -> list[date]:
        return default_slot_dates(year)


@dataclass
class SeasonInteractor:
    """What every season use case shares: the dao and the channel message."""

    dao: SeasonScheduleDao
    announcer: SeasonAnnouncer

    async def _get_season(self, year: int) -> season_dto.Season:
        season = await self.dao.get_season(year)
        if season is None:
            raise exceptions.SeasonNotFound(text=f"no season for {year}")
        return season

    @staticmethod
    def _get_slot(season: season_dto.Season, slot_id: int) -> season_dto.Slot:
        for slot in season.slots:
            if slot.id == slot_id:
                return slot
        raise exceptions.SlotNotFound(text=f"season {season.year} has no slot {slot_id}")

    async def _record(
        self,
        season: season_dto.Season,
        type_: season_dto.ChangeType,
        *,
        slot_id: int | None,
        actor: dto.Player,
        payload: dict[str, Any],
    ) -> None:
        # the audit trail shares the transaction with the write it describes
        await self.dao.add_change(
            season_id=season.id,
            type_=type_,
            slot_id=slot_id,
            actor_id=actor.id,
            payload=payload,
        )
        await self.dao.touch_season(season.id)

    async def _announce_update(self, year: int) -> None:
        """Post-commit and best-effort: the pin must show current truth."""
        try:
            season = await self.dao.get_season(year)
            if season is not None:
                await self.announcer.update(season)
        except Exception as e:  # noqa: BLE001
            logger.warning("can't update the schedule message of %s", year, exc_info=e)


@dataclass
class GetSeasonInteractor(SeasonInteractor):
    async def __call__(self, year: int) -> season_dto.Season:
        return await self._get_season(year)


@dataclass
class GetCurrentSeasonInteractor(SeasonInteractor):
    async def __call__(self, now: datetime) -> season_dto.Season:
        return await self._get_season(now.astimezone(tz_game).year)


@dataclass
class ListSeasonsInteractor:
    dao: SeasonScheduleDao

    async def __call__(self) -> Sequence[int]:
        return await self.dao.get_season_years()


@dataclass
class PublishSeasonInteractor(SeasonInteractor):
    """Create the season and all its dates in one transaction, then announce."""

    async def __call__(
        self,
        year: int,
        slots: Sequence[season_dto.SlotDraft],
        identity: IdentityProvider,
    ) -> season_dto.Season:
        author = await identity.get_required_player()
        check_can_edit_schedule(author)
        if not slots:
            raise exceptions.SeasonError(player=author, text="a season needs at least one date")
        for draft in slots:
            _check_slot_year(year, draft.date, author)
        if await self.dao.get_season(year) is not None:
            raise exceptions.SeasonAlreadyExists(player=author, text=f"season {year} exists")
        season = await self.dao.create_season(year, published_by_id=author.id)
        for draft in sorted(slots, key=lambda draft: draft.date):
            await self.dao.add_slot(season.id, draft.date, draft.note)
        await self.dao.commit()

        published = await self._get_season(year)
        await self._announce_published(published)
        await self._notify(
            published,
            actor=author,
            payload={"year": year, "published": True, "slots": len(published.slots)},
        )
        return await self._get_season(year)

    async def _announce_published(self, season: season_dto.Season) -> None:
        # a channel that refuses the post must not roll back a published season
        try:
            announcement = await self.announcer.publish(season)
        except Exception as e:  # noqa: BLE001
            logger.warning("can't announce season %s", season.year, exc_info=e)
            return
        if announcement is None:
            return
        await self.dao.set_announcement(
            season.id, chat_id=announcement.chat_id, message_id=announcement.message_id
        )
        await self.dao.commit()

    async def _notify(
        self, season: season_dto.Season, *, actor: dto.Player, payload: dict[str, Any]
    ) -> None:
        recipients = await self.dao.get_recipient_ids(_audience_since(season.published_at))
        await self.dao.create_for_recipients(
            recipient_ids=recipients,
            type_=NotificationType.season_schedule_changed,
            severity=NotificationSeverity.low,
            actor_id=actor.id,
            payload=payload,
        )
        await self.dao.commit()


@dataclass
class AddSlotInteractor(SeasonInteractor):
    async def __call__(
        self, year: int, day: date, note: str | None, identity: IdentityProvider
    ) -> season_dto.Slot:
        author = await identity.get_required_player()
        check_can_edit_schedule(author)
        _check_slot_year(year, day, author)
        season = await self._get_season(year)
        slot = await self.dao.add_slot(season.id, day, note)
        await self._record(
            season,
            season_dto.ChangeType.slot_added,
            slot_id=slot.id,
            actor=author,
            payload={"date": day.isoformat(), "note": note},
        )
        await self.dao.commit()
        await self._announce_update(year)
        return await self.dao.get_slot(slot.id)


@dataclass
class MoveSlotInteractor(SeasonInteractor):
    async def __call__(
        self, year: int, slot_id: int, day: date, identity: IdentityProvider
    ) -> season_dto.Slot:
        author = await identity.get_required_player()
        season = await self._get_season(year)
        slot = self._get_slot(season, slot_id)
        check_can_edit_schedule(author)
        _check_slot_year(year, day, author)
        if slot.date == day:
            return slot
        # read what the payload needs before the write that changes it
        previous = slot.date
        await self.dao.move_slot(slot_id, day)
        await self._record(
            season,
            season_dto.ChangeType.slot_moved,
            slot_id=slot_id,
            actor=author,
            payload={
                "from": previous.isoformat(),
                "to": day.isoformat(),
                "date": day.isoformat(),
            },
        )
        await self.dao.commit()
        await self._announce_update(year)
        return await self.dao.get_slot(slot_id)


@dataclass
class EditSlotNoteInteractor(SeasonInteractor):
    async def __call__(
        self, year: int, slot_id: int, note: str | None, identity: IdentityProvider
    ) -> season_dto.Slot:
        author = await identity.get_required_player()
        season = await self._get_season(year)
        slot = self._get_slot(season, slot_id)
        check_can_edit_schedule(author)
        await self.dao.set_slot_note(slot_id, note)
        await self._record(
            season,
            season_dto.ChangeType.slot_note_changed,
            slot_id=slot_id,
            actor=author,
            payload={"date": slot.date.isoformat(), "note": note},
        )
        await self.dao.commit()
        await self._announce_update(year)
        return await self.dao.get_slot(slot_id)


@dataclass
class RemoveSlotInteractor(SeasonInteractor):
    async def __call__(self, year: int, slot_id: int, identity: IdentityProvider) -> None:
        author = await identity.get_required_player()
        season = await self._get_season(year)
        slot = self._get_slot(season, slot_id)
        check_can_edit_schedule(author)
        # the change row outlives the date it describes, holding its payload
        await self._record(
            season,
            season_dto.ChangeType.slot_removed,
            slot_id=slot_id,
            actor=author,
            payload={"date": slot.date.isoformat()},
        )
        await self.dao.remove_slot(slot_id)
        await self.dao.commit()
        await self._announce_update(year)


@dataclass
class TakeSlotInteractor(SeasonInteractor):
    """Claim a free date, or re-take your own to change its author or orgs."""

    async def __call__(
        self,
        year: int,
        slot_id: int,
        *,
        author_kind: season_dto.SlotAuthorKind,
        team_id: int | None,
        org_player_ids: Collection[int],
        identity: IdentityProvider,
    ) -> season_dto.Slot:
        actor = await identity.get_required_player()
        season = await self._get_season(year)
        self._get_slot(season, slot_id)
        # whoever else is taking the same date right now waits here
        slot = await self.dao.lock_slot(slot_id)
        team = await self.dao.get_team_by_id(team_id) if team_id is not None else None
        check_can_take_slot(actor, author_kind=author_kind, team=team)
        await self.dao.take_slot(
            slot_id,
            owner_id=actor.id,
            author_kind=author_kind,
            team_id=team.id if author_kind == season_dto.SlotAuthorKind.team and team else None,
        )
        orgs = [await self.dao.get_player_by_id(id_) for id_ in dict.fromkeys(org_player_ids)]
        await self.dao.set_slot_orgs(slot_id, [org.id for org in orgs])
        await self._record(
            season,
            season_dto.ChangeType.slot_taken,
            slot_id=slot_id,
            actor=actor,
            payload={
                "date": slot.date.isoformat(),
                "author": team.name if team is not None else actor.name_mention,
                "author_kind": author_kind.name,
                "orgs": [org.name_mention for org in orgs],
            },
        )
        await self.dao.commit()
        await self._announce_update(year)
        return await self.dao.get_slot(slot_id)


@dataclass
class ReleaseSlotInteractor(SeasonInteractor):
    async def __call__(
        self, year: int, slot_id: int, identity: IdentityProvider
    ) -> season_dto.Slot:
        actor = await identity.get_required_player()
        season = await self._get_season(year)
        slot = self._get_slot(season, slot_id)
        check_can_edit_schedule(actor)
        if slot.is_linked:
            raise exceptions.SlotAlreadyLinked(
                player=actor, text="unlink the game before releasing the date"
            )
        released_from = slot.author_name
        await self.dao.release_slot(slot_id)
        await self.dao.set_slot_orgs(slot_id, [])
        await self._record(
            season,
            season_dto.ChangeType.slot_released,
            slot_id=slot_id,
            actor=actor,
            payload={"date": slot.date.isoformat(), "author": released_from},
        )
        await self.dao.commit()
        await self._announce_update(year)
        return await self.dao.get_slot(slot_id)


@dataclass
class SetSlotOrgsInteractor(SeasonInteractor):
    async def __call__(
        self,
        year: int,
        slot_id: int,
        org_player_ids: Collection[int],
        identity: IdentityProvider,
    ) -> season_dto.Slot:
        actor = await identity.get_required_player()
        season = await self._get_season(year)
        slot = self._get_slot(season, slot_id)
        check_can_edit_schedule(actor)
        # being named on a date is not being an author: no promotion required
        orgs = [await self.dao.get_player_by_id(id_) for id_ in dict.fromkeys(org_player_ids)]
        await self.dao.set_slot_orgs(slot_id, [org.id for org in orgs])
        await self._record(
            season,
            season_dto.ChangeType.slot_orgs_changed,
            slot_id=slot_id,
            actor=actor,
            payload={
                "date": slot.date.isoformat(),
                "orgs": [org.name_mention for org in orgs],
            },
        )
        await self.dao.commit()
        await self._announce_update(year)
        return await self.dao.get_slot(slot_id)


@dataclass
class FindSlotsNearGameStartInteractor:
    """Read-only: what the edges offer when a game start is planned."""

    dao: SeasonScheduleDao

    async def __call__(
        self,
        at: datetime,
        identity: IdentityProvider,
        window: timedelta = SLOT_SUGGEST_WINDOW,
    ) -> list[season_dto.Slot]:
        player = await identity.get_player()
        local = at.astimezone(tz_game).date()
        season = await self.dao.get_season(local.year)
        if season is None:
            return []
        return find_slots_near(season.slots, local, player, window)


@dataclass
class LinkGameToSlotInteractor(SeasonInteractor):
    async def __call__(
        self, year: int, slot_id: int, game_id: int, identity: IdentityProvider
    ) -> season_dto.Slot:
        actor = await identity.get_required_player()
        season = await self._get_season(year)
        self._get_slot(season, slot_id)
        game = await self.dao.get_game_by_id(game_id)
        occupied = await self.dao.get_slot_by_game(game_id)
        if occupied is not None and occupied.id != slot_id:
            raise exceptions.GameAlreadyInSchedule(
                player=actor,
                game=game,
                text=f"game {game_id} already sits in slot {occupied.id}",
            )
        slot = await self.dao.lock_slot(slot_id)
        if slot.is_linked and slot.game is not None and slot.game.id != game_id:
            raise exceptions.SlotAlreadyLinked(
                player=actor, text=f"slot {slot_id} already holds game {slot.game.id}"
            )
        check_can_edit_schedule(actor)
        if slot.is_free:
            # the date follows the game, so it belongs to whoever wrote it
            await self.dao.take_slot(
                slot_id,
                owner_id=game.author.id,
                author_kind=season_dto.SlotAuthorKind.player,
                team_id=None,
            )
        await self.dao.link_game(slot_id, game_id)
        await self._record(
            season,
            season_dto.ChangeType.slot_game_linked,
            slot_id=slot_id,
            actor=actor,
            payload={
                "date": slot.date.isoformat(),
                "game": game.name,
                "game_id": game.id,
            },
        )
        await self._follow_game(season, slot, game, actor=actor)
        await self.dao.commit()
        await self._announce_update(year)
        return await self.dao.get_slot(slot_id)

    async def _follow_game(
        self,
        season: season_dto.Season,
        slot: season_dto.Slot,
        game: dto.Game,
        *,
        actor: dto.Player,
    ) -> None:
        if game.start_at is None:
            return
        started = game.start_at.astimezone(tz_game).date()
        if started == slot.date:
            return
        previous = slot.date
        await self.dao.move_slot(slot.id, started)
        await self._record(
            season,
            season_dto.ChangeType.slot_moved,
            slot_id=slot.id,
            actor=actor,
            payload={
                "from": previous.isoformat(),
                "to": started.isoformat(),
                "date": started.isoformat(),
                "reason": "game_linked",
            },
        )


@dataclass
class UnlinkGameFromSlotInteractor(SeasonInteractor):
    async def __call__(
        self, year: int, slot_id: int, identity: IdentityProvider
    ) -> season_dto.Slot:
        actor = await identity.get_required_player()
        season = await self._get_season(year)
        slot = self._get_slot(season, slot_id)
        check_can_edit_schedule(actor)
        if slot.game is None:
            return slot
        unlinked = slot.game
        await self.dao.unlink_game(slot_id)
        await self._record(
            season,
            season_dto.ChangeType.slot_game_unlinked,
            slot_id=slot_id,
            actor=actor,
            payload={
                "date": slot.date.isoformat(),
                "game": unlinked.name,
                "game_id": unlinked.id,
            },
        )
        await self.dao.commit()
        await self._announce_update(year)
        return await self.dao.get_slot(slot_id)


@dataclass
class SyncLinkedSlotInteractor(SeasonInteractor):
    """A re-planned game drags its date along. Cancelling a start unlinks nothing.

    Returns whether the game sits in a date at all, which is what tells the
    game log to mark a start planned outside the season schedule.
    """

    async def __call__(self, game: dto.Game, actor: dto.Player) -> bool:
        if game.start_at is None:
            return False
        slot = await self.dao.get_slot_by_game(game.id)
        if slot is None:
            return False
        started = game.start_at.astimezone(tz_game).date()
        if started == slot.date:
            return True
        season = await self.dao.get_season_by_id(slot.season_id)
        if season is None:
            return True
        previous = slot.date
        await self.dao.move_slot(slot.id, started)
        await self._record(
            season,
            season_dto.ChangeType.slot_moved,
            slot_id=slot.id,
            actor=actor,
            payload={
                "from": previous.isoformat(),
                "to": started.isoformat(),
                "date": started.isoformat(),
                "reason": "game_rescheduled",
            },
        )
        await self.dao.commit()
        await self._announce_update(season.year)
        return True


@dataclass
class PublishSeasonDigestInteractor(SeasonInteractor):
    """The 10:00 MSK job: the day's net changes, and the end-of-season unpin."""

    async def __call__(self, now: datetime) -> None:
        for season_id in await self.dao.get_season_ids_with_unpublished_changes():
            await self._digest_one(season_id, now)
        await self._close_finished(now)

    async def _digest_one(self, season_id: int, now: datetime) -> None:
        season = await self.dao.get_season_by_id(season_id)
        if season is None:
            return
        changes = await self.dao.get_unpublished_changes(season_id)
        digests = collapse_changes(changes)
        # every change is accounted for, including those that collapsed to nothing
        await self.dao.mark_changes_published([change.id for change in changes])
        if digests:
            await self.dao.create_for_recipients(
                recipient_ids=await self.dao.get_recipient_ids(_audience_since(now)),
                type_=NotificationType.season_schedule_changed,
                severity=NotificationSeverity.low,
                payload={"year": season.year, "changes": len(digests)},
            )
        await self.dao.commit()
        if digests:
            await self._announce_digest(season, digests)

    async def _announce_digest(
        self, season: season_dto.Season, digests: Sequence[SlotDigest]
    ) -> None:
        # a failed post skips the day: the pinned message still shows the truth
        try:
            await self.announcer.announce_digest(season, digests)
        except Exception as e:  # noqa: BLE001
            logger.warning("can't announce the digest of %s", season.year, exc_info=e)

    async def _close_finished(self, now: datetime) -> None:
        today = now.astimezone(tz_game).date()
        for season in await self.dao.get_seasons_to_close(today):
            try:
                await self.announcer.close(season)
            except Exception as e:  # noqa: BLE001
                logger.warning("can't unpin the schedule of %s", season.year, exc_info=e)
            await self.dao.set_unpinned(season.id)
            await self.dao.commit()


def _audience_since(now: datetime) -> datetime:
    """1 January of last year, MSK — the window the digest reaches."""
    local = now.astimezone(tz_game)
    return datetime(local.year - AUDIENCE_YEARS_BACK, 1, 1, tzinfo=tz_game)


def _check_slot_year(year: int, day: date, player: dto.Player) -> None:
    if day.year != year:
        raise exceptions.SeasonError(
            player=player,
            text=f"{day.isoformat()} is not in season {year}",
            notify_user=f"Дата {day.isoformat()} не относится к сезону {year}",
        )
