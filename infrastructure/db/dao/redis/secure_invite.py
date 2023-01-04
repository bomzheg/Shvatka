import json
import secrets

from redis.asyncio.client import Redis

from shvatka.utils.exceptions import SaltNotExist

TOKEN_LEN = 32
EXPIRE_TIME = 12 * 60


class SecureInvite:
    def __init__(self, *, prefix="invite", redis: Redis):
        self.prefix = prefix
        self.redis = redis

    def _create_key(self, token: str) -> str:
        return f"{self.prefix}:{token}"

    async def save_new_invite(
        self, token_len: int = TOKEN_LEN, expire=EXPIRE_TIME, **dct: dict
    ) -> str:
        token = secrets.token_urlsafe(token_len)
        await self.redis.set(self._create_key(token), json.dumps(dct), ex=expire)
        return token

    async def get_invite(self, token: str) -> dict:
        key = self._create_key(token)
        dct_str = await self._get(key, encoding="utf-8")
        if dct_str is None:
            raise SaltNotExist(salt=token, text="this salt does not exist")
        return json.loads(dct_str)["dct"]

    async def remove_invite(self, token: str):
        await self.redis.delete(self._create_key(token))

    async def _get(self, key: str, encoding: str = "utf-8"):
        value = await self.redis.get(key)
        if value is None:
            return None
        return value.decode(encoding)
