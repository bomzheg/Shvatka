from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.crawler.models.team import ParsedTeam
from infrastructure.db import models
from shvatka.models import dto
from .base import BaseDAO


class ForumTeamDAO(BaseDAO[models.ForumTeam]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.ForumTeam, session)

    def save_parsed(self, team: ParsedTeam) -> dto.ForumTeam:
        db_team = models.ForumTeam(
            name=team.name,
            forum_id=team.id,
            url=team.url,
        )
        self._save(db_team)
        await self._flush(db_team)
        return db_team.to_dto()
