import typing
from datetime import timedelta


class RateLimiter(typing.Protocol):
    async def is_allowed(self, key: str, cooldown: timedelta) -> bool:
        raise NotImplementedError
