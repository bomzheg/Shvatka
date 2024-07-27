from datetime import datetime, tzinfo
import typing

from sqlalchemy import select, Result, ScalarResult
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.infrastructure.db import models
from shvatka.infrastructure.db.dao import BaseDAO


class AchievementDAO(BaseDAO[models.Achievement]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(models.Achievement, session=session, clock=clock)

    async def exist_type(self, achievement: enums.Achievement) -> bool:
        result: Result[tuple[models.Achievement]] = await self.session.execute(
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
        result: ScalarResult[models.Achievement] = await self.session.scalars(
            select(models.Achievement).where(models.Achievement.player_id == player.id)
        )
        achievements = result.all()
        return [achievement.to_dto(player) for achievement in achievements]
