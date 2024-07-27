from datetime import datetime, tzinfo
import typing
from sqlalchemy import select, ScalarResult
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.models import dto
from shvatka.infrastructure.db.models import Chat
from .base import BaseDAO


class ChatDao(BaseDAO[Chat]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(Chat, session, clock=clock)

    async def get_by_tg_id(self, tg_id: int) -> dto.Chat:
        chat = await self._get_by_tg_id(tg_id)
        return chat.to_dto()

    async def _get_by_tg_id(self, tg_id: int) -> Chat:
        result: ScalarResult[Chat] = await self.session.scalars(
            select(Chat).where(Chat.tg_id == tg_id)
        )
        return result.one()

    async def upsert_chat(self, chat: dto.Chat) -> dto.Chat:
        kwargs = dict(tg_id=chat.tg_id, title=chat.title, username=chat.username, type=chat.type)
        saved_chat = await self.session.execute(
            insert(Chat)
            .values(**kwargs)
            .on_conflict_do_update(
                index_elements=(Chat.tg_id,), set_=kwargs, where=Chat.tg_id == chat.tg_id
            )
            .returning(Chat)
        )
        return saved_chat.scalar_one().to_dto()

    async def update_chat_id(self, chat: dto.Chat, new_id: int):
        chat_db = await self._get_by_tg_id(chat.tg_id)
        chat_db.tg_id = new_id
        self._save(chat_db)
