import typing
from collections.abc import Sequence
from datetime import date, datetime, tzinfo
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shvatka.core.season import dto
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.models import Season, SeasonSlot

from .base import BaseDAO
from .season_slot import SLOT_OPTIONS


class SeasonDao(BaseDAO[Season]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(Season, session, clock=clock)

    async def get_season(self, year: int) -> dto.Season | None:
        return await self._load(Season.year == year)

    async def get_required_season(self, year: int) -> dto.Season:
        season = await self.get_season(year)
        if season is None:
            raise exceptions.SeasonNotFound(text=f"no season for {year}")
        return season

    async def get_season_by_id(self, season_id: int) -> dto.Season | None:
        return await self._load(Season.id == season_id)

    async def _load(self, *whereclause: Any) -> dto.Season | None:
        result = await self.session.scalars(
            select(Season)
            .where(*whereclause)
            .options(selectinload(Season.slots).options(*SLOT_OPTIONS))
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
            select(SeasonSlot.season_id, func.max(SeasonSlot.slot_date).label("last_date"))
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
            .options(selectinload(Season.slots).options(*SLOT_OPTIONS))
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
