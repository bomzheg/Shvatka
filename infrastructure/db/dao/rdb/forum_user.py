from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.crawler.models.team import ParsedPlayer
from infrastructure.db import models
from shvatka.models import dto
from .base import BaseDAO


class ForumUserDAO(BaseDAO[models.ForumUser]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.ForumUser, session)

    async def save_parsed(self, parsed: ParsedPlayer) -> dto.ForumUser:
        db_user = models.ForumUser(
            forum_id=parsed.forum_id,
            url=parsed.url,
            name=parsed.name,
            registered=parsed.registered_at,
        )
        self._save(db_user)
        await self._flush(db_user)
        return db_user.to_dto()
