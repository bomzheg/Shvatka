import logging
from dataclasses import dataclass
from typing import Iterable

from redis.asyncio.client import Redis

logger = logging.getLogger(__name__)


@dataclass
class ReleasePost:
    """Where a game's release currently stands: one message per part, in order."""

    chat_id: int
    message_ids: list[int]


class ReleasePostDao:
    """
    Keeps the messages a game's release was posted as, so they can be edited
    or deleted later. Purely the bot's bookkeeping — the game itself knows
    nothing about chats or message ids, exactly as with pinned messages.
    """

    def __init__(self, redis: Redis, prefix: str = "release_post") -> None:
        self.redis = redis
        self.prefix = prefix

    async def get(self, game_id: int) -> ReleasePost | None:
        raw = await self.redis.lrange(self._create_key(game_id), 0, -1)
        if not raw:
            return None
        chat_id, *message_ids = (int(value) for value in raw)
        return ReleasePost(chat_id=chat_id, message_ids=list(message_ids))

    async def save(self, game_id: int, chat_id: int, message_ids: Iterable[int]) -> None:
        key = self._create_key(game_id)
        # the chat leads the list, so one round trip reads the whole location
        values = [str(chat_id), *(str(message_id) for message_id in message_ids)]
        async with self.redis.pipeline() as pipe:
            pipe.delete(key)
            pipe.rpush(key, *values)
            await pipe.execute()

    async def drop(self, game_id: int) -> None:
        await self.redis.delete(self._create_key(game_id))

    def _create_key(self, game_id: int) -> str:
        return f"{self.prefix}:{game_id}"
