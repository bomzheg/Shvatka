from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao import BaseDAO
from app.models import db, dto
from app.models.dto.scn.level import LevelScenario


class LevelDao(BaseDAO[db.Level]):
    def __init__(self, session: AsyncSession):
        super().__init__(db.Level, session)

    async def upsert(self, author: dto.Player, scn: LevelScenario) -> dto.Level:
        try:
            level = await self.get_by_author_and_scn(author, scn)
        except NoResultFound:
            level = db.Level(
                author_id=author.id,
                name_id=scn.id,
            )
            self.save(level)
        level.scenario = scn
        await self.flush(level)
        return dto.Level.from_db(level, author)

    async def get_by_author_and_scn(self, author: dto.Player, scn: LevelScenario) -> db.Level:
        result = await self.session.execute(
            select(db.Level).where(
                db.Level.name_id == scn.id,
                db.Level.author_id == author.id,
            )
        )
        return result.scalar_one()
