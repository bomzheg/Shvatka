from datetime import timedelta

from redis.asyncio.client import Redis


class RateLimiter:
    def __init__(self, *, prefix: str = "rl", redis: Redis) -> None:
        self.prefix = prefix
        self.redis = redis

    def _create_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def is_allowed(self, key: str, cooldown: timedelta) -> bool:
        return bool(await self.redis.set(self._create_key(key), "1", ex=cooldown, nx=True))
