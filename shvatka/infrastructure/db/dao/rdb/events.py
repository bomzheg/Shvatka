from datetime import datetime, tzinfo
import typing

from sqlalchemy import select, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.models import dto
from shvatka.core.models.dto import action
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db import models
from .base import BaseDAO


class GameEventDao(BaseDAO[models.GameEvent]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(models.GameEvent, session, clock=clock)

    async def get_team_events(
        self,
        team: dto.Team,
        level_time: dto.LevelTime,
    ) -> list[dto.GameEvent]:
        result: ScalarResult[models.GameEvent] = await self.session.scalars(
            select(models.GameEvent).where(
                models.GameEvent.level_time_id == level_time.id,
                models.GameEvent.team_id == team.id,
            )
        )
        return [event.to_dto(team=team) for event in result.all()]

    async def save_event(
        self,
        team: dto.Team,
        level_time: dto.LevelTime,
        game: dto.Game,
        effects: action.Effects,
        at: datetime | None = None,
    ) -> dto.GameEvent:
        if at is None:
            at = self.clock(tz_utc)
        event = models.GameEvent(
            team_id=team.id,
            game_id=game.id,
            level_number=level_time.level_number,
            level_time_id=level_time.id,
            at=at,
            effects=effects,
        )
        self._save(event)
        return event.to_dto(team)
