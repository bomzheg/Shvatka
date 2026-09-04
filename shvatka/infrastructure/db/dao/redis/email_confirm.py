import json
import typing
from datetime import datetime, timedelta, tzinfo

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

    def _player_key(self, player_id: int) -> str:
        return f"{self.prefix}:player:{player_id}"

    async def save_code(self, email: str, code: str, player_id: int) -> None:
        expire = timedelta(minutes=EXPIRE_MINUTES)
        await self.redis.set(
            self._create_key(email),
            json.dumps({"code": code, "player_id": player_id}),
            ex=expire,
        )
        await self.redis.set(self._player_key(player_id), email, ex=expire)

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
        confirmation = await self.get_code(email)
        await self.redis.delete(self._create_key(email))
        if confirmation is None:
            return
        # Drop the reverse index only while it still points at this very email:
        # a newer request for another email must survive this cleanup.
        pending = await self.get_pending_email(confirmation.player_id)
        if pending == email:
            await self.redis.delete(self._player_key(confirmation.player_id))

    async def get_pending_email(self, player_id: int) -> str | None:
        value = await self.redis.get(self._player_key(player_id))
        if value is None:
            return None
        return value.decode() if isinstance(value, bytes) else str(value)
