from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.crawler.models.team import ParsedTeam
from src.infrastructure.db import models
from src.shvatka.models import dto
from .base import BaseDAO


class ForumTeamDAO(BaseDAO[models.ForumTeam]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.ForumTeam, session)

    async def upsert(self, team: ParsedTeam) -> dto.ForumTeam:
        kwargs = dict(
            name=team.name,
            forum_id=team.id,
            url=team.url,
        )
        saved_team = await self.session.scalars(
            insert(models.ForumTeam)
            .values(**kwargs)
            .on_conflict_do_update(
                index_elements=(models.ForumTeam.name,),
                set_=kwargs,
                where=models.ForumTeam.name == team.name,
            )
            .returning(models.ForumTeam)
        )
        return saved_team.one().to_dto()
