import typing
from datetime import tzinfo, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db import models
from .base import BaseDAO
from shvatka.infrastructure.db.models import TimerAction


class TimersDAO(BaseDAO[TimerAction]):
    def __init__(self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime]):
        super().__init__(TimerAction, session, clock=clock)

    async def save_timer(
        self,
        level_time: dto.LevelTime,
        event: dto.GameEvent,
        at: datetime | None = None,
    ) -> dto.Timer:
        if at is None:
            at = self.clock(tz_utc)
        timer = models.TimerAction(
            level_time_id=level_time.id,
            started_at=at,
            event_id=event.id,
        )
        self._save(timer)
        return timer.to_dto(event)
