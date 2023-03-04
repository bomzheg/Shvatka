from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import dto
from src.infrastructure.crawler.models.team import ParsedPlayer
from src.infrastructure.db import models
from .base import BaseDAO


class ForumUserDAO(BaseDAO[models.ForumUser]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.ForumUser, session)

    async def upsert(self, parsed: ParsedPlayer) -> dto.ForumUser:
        kwargs = dict(
            forum_id=parsed.forum_id,
            url=parsed.url,
            name=parsed.name,
            registered=parsed.registered_at,
        )
        saved_team = await self.session.scalars(
            insert(models.ForumUser)
            .values(**kwargs)
            .on_conflict_do_update(
                index_elements=(models.ForumUser.name,),
                set_=kwargs,
                where=models.ForumUser.name == parsed.name,
            )
            .returning(models.ForumUser)
        )
        return saved_team.one().to_dto()
