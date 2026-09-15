import typing
from collections.abc import Collection, Sequence
from datetime import datetime, tzinfo
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.season import dto
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.models import SeasonChange

from .base import BaseDAO


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
        payload: dict[str, Any] | None = None,
    ) -> dto.ScheduleChange:
        change = SeasonChange(
            season_id=season_id,
            slot_id=slot_id,
            type=type_.name,
            actor_id=actor_id,
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
