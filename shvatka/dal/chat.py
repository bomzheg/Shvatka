from shvatka.dal.base import Committer
from shvatka.models import dto


class ChatUpserter(Committer):
    async def upsert_chat(self, chat: dto.Chat) -> dto.Chat:
        pass


class ChatIdUpdater(Committer):
    async def update_chat_id(self, chat: dto.Chat, new_id: int) -> None:
        pass
