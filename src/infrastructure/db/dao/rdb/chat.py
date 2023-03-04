from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import dto
from src.infrastructure.db.models import Chat
from .base import BaseDAO


class ChatDao(BaseDAO[Chat]):
    def __init__(self, session: AsyncSession):
        super().__init__(Chat, session)

    async def get_by_tg_id(self, tg_id: int) -> dto.Chat:
        chat = await self._get_by_tg_id(tg_id)
        return chat.to_dto()

    async def _get_by_tg_id(self, tg_id: int) -> Chat:
        result = await self.session.execute(select(Chat).where(Chat.tg_id == tg_id))
        return result.scalar_one()

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
