import typing
from datetime import date, datetime, tzinfo
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from shvatka.core.season import dto
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.models import Player, SeasonSlot, SeasonSlotOrg, Team

from .base import BaseDAO

SLOT_OPTIONS = (
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

LOCK_NOT_AVAILABLE = "55P03"
"""Postgres says the row is being edited by a transaction that has not finished."""


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
        """Take the row lock first, then read it back with everything attached.

        `nowait` rather than a wait: whoever queues behind an open edit would
        read the row as it was *before* that edit and write their own version
        over it. Failing is the honest answer — the caller re-reads and decides
        again against what is actually there.
        """
        try:
            locked = await self.session.execute(
                select(SeasonSlot.id).where(SeasonSlot.id == slot_id).with_for_update(nowait=True)
            )
        except DBAPIError as e:
            if getattr(e.orig, "sqlstate", None) != LOCK_NOT_AVAILABLE:
                raise
            raise exceptions.SlotIsBusy(text=f"slot {slot_id} is being edited right now") from e
        if locked.scalar_one_or_none() is None:
            raise exceptions.SlotNotFound(text=f"no slot {slot_id}")
        return await self.get_slot(slot_id)

    async def _get_slot_model(self, *whereclause: Any) -> SeasonSlot | None:
        result = await self.session.scalars(
            select(SeasonSlot).where(*whereclause).options(*SLOT_OPTIONS)
        )
        return result.unique().one_or_none()

    async def add_slot(self, season_id: int, day: date, note: str | None = None) -> dto.Slot:
        slot = SeasonSlot(season_id=season_id, slot_date=day, note=note)
        self._save(slot)
        await self._flush(slot)
        return dto.Slot(id=slot.id, season_id=season_id, slot_date=day, note=note)

    async def move_slot(self, slot_id: int, day: date) -> None:
        await self._update(slot_id, slot_date=day)

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
