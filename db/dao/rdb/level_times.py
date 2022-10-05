from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

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
        self.session.add(level_time)
