from typing import Protocol

from src.shvatka.interfaces.dal.base import Committer
from src.shvatka.models import dto


class ChatUpserter(Committer, Protocol):
    async def upsert_chat(self, chat: dto.Chat) -> dto.Chat:
        raise NotImplementedError


class ChatIdUpdater(Committer, Protocol):
    async def update_chat_id(self, chat: dto.Chat, new_id: int) -> None:
        raise NotImplementedError
