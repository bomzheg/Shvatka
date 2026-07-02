import json
import typing
from datetime import datetime, tzinfo, timedelta

from redis.asyncio.client import Redis

from shvatka.core.models import dto

EXPIRE_MINUTES = 30


class EmailConfirmationStore:
    def __init__(
        self,
        *,
        prefix: str = "email_confirm",
        redis: Redis,
        clock: typing.Callable[[tzinfo], datetime] = datetime.now,
    ) -> None:
        self.prefix = prefix
        self.redis = redis
        self.clock = clock

    def _create_key(self, email: str) -> str:
        return f"{self.prefix}:{email}"

    async def save_code(self, email: str, code: str, player_id: int) -> None:
        await self.redis.set(
            self._create_key(email),
            json.dumps({"code": code, "player_id": player_id}),
            ex=timedelta(minutes=EXPIRE_MINUTES),
        )

    async def get_code(self, email: str) -> dto.EmailConfirmation | None:
        value = await self.redis.get(self._create_key(email))
        if value is None:
            return None
        data = json.loads(value)
        return dto.EmailConfirmation(
            email=email,
            code=data["code"],
            player_id=data["player_id"],
        )

    async def remove_code(self, email: str) -> None:
        await self.redis.delete(self._create_key(email))
