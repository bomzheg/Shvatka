from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from infrastructure.db import models
from shvatka.models import dto
from shvatka.utils.datetime_utils import tz_utc
from .base import BaseDAO


class LevelTimeDao(BaseDAO[models.LevelTime]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.LevelTime, session)

    async def set_to_level(self, team: dto.Team, game: dto.Game, level_number: int):
        level_time = models.LevelTime(
            game_id=game.id,
            team_id=team.id,
            level_number=level_number,
            start_at=datetime.now(tz=tz_utc),
        )
        self._save(level_time)

    async def is_team_on_level(self, team: dto.Team, level: dto.Level) -> bool:
        return (
            await self._get_current(team.id, level.game_id)
        ).level_number == level.number_in_game

    async def get_current_level(self, team: dto.Team, game: dto.Game) -> int:
        return (await self.get_current_level_time(team=team, game=game)).level_number

    async def get_current_level_time(self, team: dto.Team, game: dto.Game) -> dto.LevelTime:
        db: models.LevelTime = await self._get_current(team.id, game.id)
        return db.to_dto(team=team, game=game)

    async def _get_current(self, team_id: int, game_id: int) -> models.LevelTime:
        result = await self.session.execute(
            select(models.LevelTime)
            .where(
                models.LevelTime.team_id == team_id,
                models.LevelTime.game_id == game_id,
            )
            .order_by(models.LevelTime.level_number.desc())  # noqa
            .limit(1)
        )
        return result.scalar_one()

    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        result = await self.session.scalars(
            select(models.LevelTime)
            .where(models.LevelTime.game_id == game.id)
            .options(
                joinedload(models.LevelTime.team)
                .joinedload(models.Team.captain)
                .joinedload(models.Player.user),
                joinedload(models.LevelTime.team).joinedload(models.Team.chat),
            )
            .order_by(
                models.LevelTime.team_id,
                models.LevelTime.level_number,
            )
        )
        return [
            lt.to_dto(
                game=game,
                team=lt.team.to_dto(lt.team.chat.to_dto()),
            )
            for lt in result.all()
        ]
