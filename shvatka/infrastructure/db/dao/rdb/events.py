import typing
from datetime import datetime, tzinfo

from sqlalchemy import ScalarResult, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shvatka.core.games.dto import BonusEvent, BonusSource, Event
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

    async def get_team_level_events(
        self,
        team: dto.Team,
        level_time: dto.LevelTime,
    ) -> list[dto.GameEvent]:
        result: ScalarResult[models.GameEvent] = await self.session.scalars(
            select(models.GameEvent)
            .where(
                models.GameEvent.game_id == level_time.game.id,
                models.GameEvent.level_time_id == level_time.id,
                models.GameEvent.team_id == team.id,
            )
            .order_by(models.GameEvent.at.desc())
        )
        return [event.to_dto() for event in result.all()]

    async def get_team_events(
        self,
        team: dto.Team,
        game_id: int,
    ) -> list[dto.GameEvent]:
        result: ScalarResult[models.GameEvent] = await self.session.scalars(
            select(models.GameEvent)
            .where(
                models.GameEvent.game_id == game_id,
                models.GameEvent.team_id == team.id,
            )
            .order_by(models.GameEvent.at.desc())
        )
        return [event.to_dto() for event in result.all()]

    async def get_team_events_with_source(self, team: dto.Team, game_id: int) -> list[Event]:
        result: ScalarResult[models.GameEvent] = await self.session.scalars(
            select(models.GameEvent)
            .options(
                joinedload(models.GameEvent.key),
                joinedload(models.GameEvent.timer),
            )
            .where(
                models.GameEvent.game_id == game_id,
                models.GameEvent.team_id == team.id,
            )
            .order_by(models.GameEvent.at.desc())
        )
        return [self.map_to_event(event) for event in result.all()]

    async def get_game_bonuses_by_teams(self, game: dto.Game) -> dict[int, list[BonusEvent]]:
        """All teams' bonuses and penalties for the game, grouped by team id."""
        result: ScalarResult[models.GameEvent] = await self.session.scalars(
            select(models.GameEvent)
            .options(
                joinedload(models.GameEvent.key),
                joinedload(models.GameEvent.timer),
            )
            .where(models.GameEvent.game_id == game.id)
            .order_by(models.GameEvent.at)
        )
        bonuses: dict[int, list[BonusEvent]] = {}
        for event in result.all():
            if not event.effects.bonus_minutes:
                continue
            bonuses.setdefault(event.team_id, []).append(self.map_to_bonus(event))
        return bonuses

    def map_to_bonus(self, event: models.GameEvent) -> BonusEvent:
        return BonusEvent(
            at=event.at,
            effects=event.effects,
            source=self._resolve_source(event),
            key=event.key.key_text if event.key else None,
            level_time_id=event.level_time_id,
        )

    @staticmethod
    def _resolve_source(event: models.GameEvent) -> BonusSource:
        if event.key is not None:
            return BonusSource.key
        if event.timer is not None:
            return BonusSource.timer
        return BonusSource.unknown

    def map_to_event(self, event: models.GameEvent) -> Event:
        return Event(
            id=event.id,
            level_time_id=event.level_time_id,
            at=event.at,
            effects=event.effects,
            key=event.key.key_text if event.key else None,
            is_timer=event.timer is not None,
        )

    async def save_event(
        self,
        team: dto.Team,
        game: dto.Game,
        level_time: dto.LevelTime,
        effects: action.Effects,
        at: datetime | None = None,
    ) -> dto.GameEvent:
        if at is None:
            at = self.clock(tz_utc)
        event = models.GameEvent(
            team_id=team.id,
            game_id=game.id,
            level_time_id=level_time.id,
            at=at,
            effects=effects,
        )
        self._save(event)
        await self._flush(event)
        return event.to_dto()
