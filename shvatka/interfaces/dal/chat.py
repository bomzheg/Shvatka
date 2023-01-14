from typing import Protocol

from shvatka.interfaces.dal.base import Committer
from shvatka.models import dto


class ChatUpserter(Protocol, Committer):
    async def upsert_chat(self, chat: dto.Chat) -> dto.Chat:
        raise NotImplementedError


class ChatIdUpdater(Protocol, Committer):
    async def update_chat_id(self, chat: dto.Chat, new_id: int) -> None:
        raise NotImplementedError
