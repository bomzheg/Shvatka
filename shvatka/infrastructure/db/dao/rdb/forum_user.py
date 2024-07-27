from datetime import datetime, tzinfo
import typing
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.models import dto
from shvatka.infrastructure.crawler.models.team import ParsedPlayer
from shvatka.infrastructure.db import models
from .base import BaseDAO


class ForumUserDAO(BaseDAO[models.ForumUser]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(models.ForumUser, session, clock=clock)

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

    async def get_by_id(self, id_: int) -> dto.ForumUser:
        result = await self._get_by_id(id_)
        return result.to_dto()

    async def get_by_forum_id(self, forum_id: int) -> dto.ForumUser:
        result = await self.session.scalars(
            select(models.ForumUser).where(models.ForumUser.forum_id == forum_id)
        )
        return result.one().to_dto()

    async def replace_player(self, primary: dto.Player, secondary: dto.Player) -> None:
        await self.session.execute(
            update(models.ForumUser)
            .where(models.ForumUser.player_id == secondary.id)
            .values(player_id=primary.id)
        )
