from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models
from shvatka.models import dto
from .base import BaseDAO


class LevelTimeDao(BaseDAO[models.LevelTime]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.LevelTime, session)

    async def set_to_level(self, team: dto.Team, game: dto.Game, level_number: int):
        level_time = models.LevelTime(
            game_id=game.id,
            team_id=team.id,
            level_number=level_number,
            start_at=datetime.utcnow(),
        )
        self._save(level_time)

    async def is_team_on_level(self, team: dto.Team, level: dto.Level) -> bool:
        return await self.get_current_level(team=team, game_id=level.game_id) == level.number_in_game

    async def get_current_level(self, team: dto.Team, game_id: int) -> int:
        result = await self.session.execute(
            select(models.LevelTime)
            .where(
                models.LevelTime.team_id == team.id,
                models.LevelTime.game_id == game_id,
            )
            .order_by(models.LevelTime.level_number.desc())  # noqa
            .limit(1)
        )
        return result.scalar_one().level_number

