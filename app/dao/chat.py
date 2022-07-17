from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.dao import BaseDAO
from app.models import dto
from app.models.db import Chat


class ChatDao(BaseDAO[Chat]):
    def __init__(self, session: AsyncSession):
        super().__init__(Chat, session)

    async def get_by_tg_id(self, tg_id: int) -> Chat:
        result = await self.session.execute(
            select(Chat).where(Chat.tg_id == tg_id)
        )
        return result.scalar_one()

    async def upsert_chat(self, chat: dto.Chat) -> dto.Chat:
        try:
            saved_chat = await self.get_by_tg_id(chat.tg_id)
        except NoResultFound:
            saved_chat = Chat(tg_id=chat.tg_id)
        was_changed = update_fields(chat, saved_chat)
        if was_changed:
            self.save(saved_chat)
            await self.flush(saved_chat)
        return dto.Chat.from_db(saved_chat)

    async def update_chat_id(self, chat: dto.Chat, new_id: int):
        chat_db = await self.get_by_tg_id(chat.tg_id)
        chat_db.tg_id = new_id
        self.save(chat_db)


def update_fields(source: dto.Chat, target: Chat):
    if all([
        target.title == source.title,
        target.username == source.username,
        target.type == source.type
    ]):
        return False
    target.title = source.name
    target.username = source.username
    target.type = source.type
    return True
