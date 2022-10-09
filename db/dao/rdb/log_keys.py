from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models
from shvatka.models import dto
from .base import BaseDAO


class KeyTimeDao(BaseDAO[models.KeyTime]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.KeyTime, session)

    async def get_correct_typed_keys(self, level: dto.Level, game: dto.Game, team: dto.Team) -> set[str]:
        result = await self.session.execute(
            select(models.KeyTime)
            .where(
                models.KeyTime.game_id == game.id,
                models.KeyTime.level_number == level.number_in_game,
                models.KeyTime.team_id == team.id,
                models.KeyTime.is_correct.is_(True),  # noqa
            )
        )
        return {key.key_text for key in result.scalars().all()}

    async def save_key(self, key: str, team: dto.Team, level: dto.Level, game: dto.Game, player: dto.Player,
                       is_correct: bool) -> None:
        key_time = models.KeyTime(
            key_text=key,
            team_id=team.id,
            level_number=level.number_in_game,
            game_id=game.id,
            player_id=player.id,
            is_correct=is_correct,
            enter_time=datetime.utcnow(),
        )
        self._save(key_time)
