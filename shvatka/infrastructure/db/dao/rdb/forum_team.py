from typing import Sequence

from sqlalchemy import update, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from shvatka.core.models import dto
from shvatka.infrastructure.crawler.models.team import ParsedTeam
from shvatka.infrastructure.db import models
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

    async def replace_forum_team(self, primary: dto.Team, secondary: dto.Team):
        await self.session.execute(
            update(models.ForumTeam)
            .where(models.ForumTeam.team_id == secondary.id)
            .values(team_id=primary.id)
        )

    async def get_free_forum_teams(self) -> Sequence[dto.ForumTeam]:
        result = await self.session.scalars(
            select(models.ForumTeam)
            .join(models.ForumTeam.team)
            .options(contains_eager(models.ForumTeam.team))
            .where(models.Team.is_dummy.is_(True))
            .order_by(models.ForumTeam.id)
            .distinct(models.ForumTeam.id)
        )
        return list(map(models.ForumTeam.to_dto, result.all()))
