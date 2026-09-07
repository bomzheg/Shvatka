import typing
from collections.abc import Collection, Sequence
from datetime import date, datetime, tzinfo
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from shvatka.core.season import dto
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.models import (
    Player,
    Season,
    SeasonChange,
    SeasonSlot,
    SeasonSlotOrg,
    Team,
)

from .base import BaseDAO

_SLOT_OPTIONS = (
    # `to_dto` walks into the owner's user, the team's chat and captain, and
    # every org's user — an async session raises rather than lazy-loading any
    # of them, so each one is asked for here
    joinedload(SeasonSlot.owner).joinedload(Player.user),
    joinedload(SeasonSlot.team).joinedload(Team.chat),
    joinedload(SeasonSlot.team).joinedload(Team.forum_team),
    joinedload(SeasonSlot.team).joinedload(Team.captain).joinedload(Player.user),
    joinedload(SeasonSlot.game),
    selectinload(SeasonSlot.orgs).joinedload(SeasonSlotOrg.player).joinedload(Player.user),
)


class SeasonDao(BaseDAO[Season]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(Season, session, clock=clock)

    async def get_season(self, year: int) -> dto.Season | None:
        return await self._load(Season.year == year)

    async def get_season_by_id(self, season_id: int) -> dto.Season | None:
        return await self._load(Season.id == season_id)

    async def _load(self, *whereclause: Any) -> dto.Season | None:
        result = await self.session.scalars(
            select(Season)
            .where(*whereclause)
            .options(selectinload(Season.slots).options(*_SLOT_OPTIONS))
        )
        season = result.unique().one_or_none()
        if season is None:
            return None
        return season.to_dto_with_slots()

    async def get_season_years(self) -> Sequence[int]:
        result = await self.session.scalars(select(Season.year).order_by(Season.year.desc()))
        return list(result.all())

    async def get_seasons_to_close(self, today: date) -> Sequence[dto.Season]:
        """Announced seasons still pinned whose latest date is behind us."""
        last_date = (
            select(SeasonSlot.season_id, func.max(SeasonSlot.date).label("last_date"))
            .group_by(SeasonSlot.season_id)
            .subquery()
        )
        result = await self.session.scalars(
            select(Season)
            .join(last_date, last_date.c.season_id == Season.id)
            .where(
                Season.unpinned_at.is_(None),
                Season.log_message_id.is_not(None),
                last_date.c.last_date < today,
            )
            .options(selectinload(Season.slots).options(*_SLOT_OPTIONS))
        )
        return [season.to_dto_with_slots() for season in result.unique().all()]

    async def create_season(self, year: int, published_by_id: int) -> dto.Season:
        season = Season(year=year, published_by_id=published_by_id)
        self._save(season)
        await self._flush(season)
        return season.to_dto()

    async def set_announcement(self, season_id: int, *, chat_id: int, message_id: int) -> None:
        await self.session.execute(
            update(Season)
            .where(Season.id == season_id)
            .values(log_chat_id=chat_id, log_message_id=message_id)
        )

    async def set_unpinned(self, season_id: int) -> None:
        await self.session.execute(
            update(Season).where(Season.id == season_id).values(unpinned_at=self.clock(tz_utc))
        )

    async def touch_season(self, season_id: int) -> None:
        await self.session.execute(
            update(Season).where(Season.id == season_id).values(updated_at=self.clock(tz_utc))
        )


class SeasonSlotDao(BaseDAO[SeasonSlot]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(SeasonSlot, session, clock=clock)

    async def get_slot(self, slot_id: int) -> dto.Slot:
        slot = await self._get_slot_model(SeasonSlot.id == slot_id)
        if slot is None:
            raise exceptions.SlotNotFound(text=f"no slot {slot_id}")
        return slot.to_dto()

    async def get_slot_by_game(self, game_id: int) -> dto.Slot | None:
        slot = await self._get_slot_model(SeasonSlot.game_id == game_id)
        return slot.to_dto() if slot is not None else None

    async def lock_slot(self, slot_id: int) -> dto.Slot:
        """Take the row lock first, then read it back with everything attached."""
        locked = await self.session.execute(
            select(SeasonSlot.id).where(SeasonSlot.id == slot_id).with_for_update()
        )
        if locked.scalar_one_or_none() is None:
            raise exceptions.SlotNotFound(text=f"no slot {slot_id}")
        return await self.get_slot(slot_id)

    async def _get_slot_model(self, *whereclause: Any) -> SeasonSlot | None:
        result = await self.session.scalars(
            select(SeasonSlot).where(*whereclause).options(*_SLOT_OPTIONS)
        )
        return result.unique().one_or_none()

    async def add_slot(self, season_id: int, day: date, note: str | None = None) -> dto.Slot:
        slot = SeasonSlot(season_id=season_id, date=day, note=note)
        self._save(slot)
        await self._flush(slot)
        return dto.Slot(id=slot.id, season_id=season_id, date=day, note=note)

    async def move_slot(self, slot_id: int, day: date) -> None:
        await self._update(slot_id, date=day)

    async def set_slot_note(self, slot_id: int, note: str | None) -> None:
        await self._update(slot_id, note=note)

    async def remove_slot(self, slot_id: int) -> None:
        await self.session.execute(delete(SeasonSlot).where(SeasonSlot.id == slot_id))

    async def take_slot(
        self,
        slot_id: int,
        *,
        owner_id: int,
        author_kind: dto.SlotAuthorKind,
        team_id: int | None = None,
    ) -> None:
        await self._update(
            slot_id,
            owner_id=owner_id,
            author_kind=author_kind,
            team_id=team_id,
            taken_at=self.clock(tz_utc),
        )

    async def release_slot(self, slot_id: int) -> None:
        await self._update(slot_id, owner_id=None, author_kind=None, team_id=None, taken_at=None)

    async def link_game(self, slot_id: int, game_id: int) -> None:
        await self._update(slot_id, game_id=game_id)

    async def unlink_game(self, slot_id: int) -> None:
        await self._update(slot_id, game_id=None)

    async def _update(self, slot_id: int, **values: Any) -> None:
        # every caller has looked the slot up (or locked it) first
        await self.session.execute(
            update(SeasonSlot)
            .where(SeasonSlot.id == slot_id)
            .values(updated_at=self.clock(tz_utc), **values)
        )


class SeasonSlotOrgDao(BaseDAO[SeasonSlotOrg]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(SeasonSlotOrg, session, clock=clock)

    async def set_slot_orgs(self, slot_id: int, player_ids: Collection[int]) -> None:
        await self.session.execute(delete(SeasonSlotOrg).where(SeasonSlotOrg.slot_id == slot_id))
        for player_id in dict.fromkeys(player_ids):
            self._save(SeasonSlotOrg(slot_id=slot_id, player_id=player_id))
        await self.session.flush()


class SeasonChangeDao(BaseDAO[SeasonChange]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(SeasonChange, session, clock=clock)

    async def add_change(
        self,
        *,
        season_id: int,
        type_: dto.ChangeType,
        slot_id: int | None = None,
        actor_id: int | None = None,
        by_superuser: bool = False,
        payload: dict[str, Any] | None = None,
    ) -> dto.ScheduleChange:
        change = SeasonChange(
            season_id=season_id,
            slot_id=slot_id,
            type=type_.name,
            actor_id=actor_id,
            by_superuser=by_superuser,
            payload=payload or {},
        )
        self._save(change)
        await self._flush(change)
        return change.to_dto()

    async def get_unpublished_changes(self, season_id: int) -> Sequence[dto.ScheduleChange]:
        result = await self.session.scalars(
            select(SeasonChange)
            .where(SeasonChange.season_id == season_id, SeasonChange.published_at.is_(None))
            .order_by(SeasonChange.created_at, SeasonChange.id)
        )
        return [change.to_dto() for change in result.all()]

    async def get_season_ids_with_unpublished_changes(self) -> Sequence[int]:
        result = await self.session.scalars(
            select(SeasonChange.season_id)
            .where(SeasonChange.published_at.is_(None))
            .group_by(SeasonChange.season_id)
        )
        return list(result.all())

    async def mark_changes_published(self, change_ids: Collection[int]) -> None:
        if not change_ids:
            return
        await self.session.execute(
            update(SeasonChange)
            .where(SeasonChange.id.in_(change_ids), SeasonChange.published_at.is_(None))
            .values(published_at=self.clock(tz_utc))
        )
