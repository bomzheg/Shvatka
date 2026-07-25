import logging
from datetime import timedelta
from typing import Iterable

from redis.asyncio.client import Redis

logger = logging.getLogger(__name__)


class PinnedMessageDao:
    """
    Keeps ids of messages pinned by the bot, so they can be unpinned later.
    Messages are grouped by chat and category (e.g. hints of a level are
    unpinned on level up, while bonus hints are unpinned at the end of a game).
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
        """Returns all saved ids and forgets them."""
        key = self._create_key(chat_id=chat_id, category=category)
        message_ids = await self.redis.lrange(key, 0, -1)
        await self.redis.delete(key)
        return [int(message_id) for message_id in message_ids]

    def _create_key(self, chat_id: int, category: str) -> str:
        return f"{self.prefix}:{category}:{chat_id}"
