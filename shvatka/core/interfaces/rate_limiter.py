import typing
from datetime import timedelta


class RateLimiter(typing.Protocol):
    async def is_allowed(self, key: str, cooldown: timedelta) -> bool:
        """Mark `key` as used and return True, unless it was already used within `cooldown`."""
        raise NotImplementedError
