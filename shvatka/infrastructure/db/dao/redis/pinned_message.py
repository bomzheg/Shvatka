import logging
from datetime import timedelta
from typing import Iterable

from redis.asyncio.client import Redis

logger = logging.getLogger(__name__)


class PinnedMessageDao:
    """
    Хранит id закреплённых ботом сообщений, чтобы потом их можно было открепить.
    Сообщения группируются по чату и категории (например подсказки уровня
    открепляются при переходе на следующий уровень, а бонусные - в конце игры).
    """

    TTL = timedelta(days=30)

    def __init__(self, redis: Redis, prefix: str = "pinned") -> None:
        self.redis = redis
        self.prefix = prefix

    async def save(self, chat_id: int, category: str, message_ids: Iterable[int]) -> None:
        ids = [str(message_id) for message_id in message_ids]
        if not ids:
            return
        key = self._create_key(chat_id=chat_id, category=category)
        await self.redis.rpush(key, *ids)
        await self.redis.expire(key, self.TTL)

    async def pop_all(self, chat_id: int, category: str) -> list[int]:
        """Возвращает все сохранённые id и забывает их."""
        key = self._create_key(chat_id=chat_id, category=category)
        message_ids = await self.redis.lrange(key, 0, -1)
        await self.redis.delete(key)
        return [int(message_id) for message_id in message_ids]

    def _create_key(self, chat_id: int, category: str) -> str:
        return f"{self.prefix}:{category}:{chat_id}"
