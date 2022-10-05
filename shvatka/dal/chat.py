from abc import ABCMeta

from shvatka.dal.base import Committer
from shvatka.models import dto


class ChatUpserter(Committer, metaclass=ABCMeta):
    async def upsert_chat(self, chat: dto.Chat) -> dto.Chat:
        raise NotImplementedError


class ChatIdUpdater(Committer, metaclass=ABCMeta):
    async def update_chat_id(self, chat: dto.Chat, new_id: int) -> None:
        raise NotImplementedError
