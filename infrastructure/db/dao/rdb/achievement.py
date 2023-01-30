from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db import models
from infrastructure.db.dao import BaseDAO
from shvatka.models import enums, dto


class AchievementDAO(BaseDAO[models.Achievement]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Achievement, session=session)

    async def exist_type(self, achievement: enums.Achievement) -> bool:
        result = await self.session.execute(
            select(models.Achievement).where(models.Achievement.name == achievement)
        )
        try:
            result.scalar_one()
        except NoResultFound:
            return False
        else:
            return True

    async def add_achievement(self, achievement: dto.Achievement) -> None:
        db = models.Achievement(
            player_id=achievement.player.id, name=achievement.name, first=achievement.first
        )
        self._save(db)

    async def get_by_player(self, player: dto.Player) -> list[dto.Achievement]:
        result = await self.session.execute(
            select(models.Achievement).where(models.Achievement.player_id == player.id)
        )
        achievements: list[models.Achievement] = result.scalars().all()
        return [achievement.to_dto(player) for achievement in achievements]
