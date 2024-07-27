from datetime import datetime, tzinfo
import typing
from sqlalchemy import select, ScalarResult, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.models import dto
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db import models
from .base import BaseDAO


class ChatDao(BaseDAO[models.Chat]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(models.Chat, session, clock=clock)

    async def get_by_tg_id(self, tg_id: int) -> dto.Chat:
        chat = await self._get_by_tg_id(tg_id)
        return chat.to_dto()

    async def _get_by_tg_id(self, tg_id: int) -> models.Chat:
        result: ScalarResult[models.Chat] = await self.session.scalars(
            select(models.Chat).where(models.Chat.tg_id == tg_id)
        )
        try:
            return result.one()
        except NoResultFound as e:
            raise exceptions.ChatNotFound(chat_id=tg_id) from e

    async def change_team_chat(self, team: dto.Team, chat: dto.Chat) -> None:
        await self.session.execute(
            update(models.Chat).where(models.Chat.tg_id == team.get_chat_id()).values(team_id=None)
        )
        await self.session.execute(
            update(models.Chat).where(models.Chat.tg_id == chat.tg_id).values(team_id=team.id)
        )

    async def upsert_chat(self, chat: dto.Chat) -> dto.Chat:
        kwargs = dict(tg_id=chat.tg_id, title=chat.title, username=chat.username, type=chat.type)
        saved_chat = await self.session.execute(
            insert(models.Chat)
            .values(**kwargs)
            .on_conflict_do_update(
                index_elements=(models.Chat.tg_id,),
                set_=kwargs,
                where=models.Chat.tg_id == chat.tg_id,
            )
            .returning(models.Chat)
        )
        return saved_chat.scalar_one().to_dto()

    async def update_chat_id(self, chat: dto.Chat, new_id: int):
        chat_db = await self._get_by_tg_id(chat.tg_id)
        chat_db.tg_id = new_id
        self._save(chat_db)
