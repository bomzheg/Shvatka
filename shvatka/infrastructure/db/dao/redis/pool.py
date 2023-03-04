import logging

from redis.asyncio.client import Redis

from shvatka.core.models.enums.played import Played

logger = logging.getLogger(__name__)


class PollDao:
    def __init__(self, redis: Redis):
        self.prefix = "poll"
        self.msg_prefix = "msg_poll"
        self.redis = redis

    async def add_player_vote(self, team_id: int, player_id: int, vote_var: str) -> None:
        key = self._create_key(team_id=team_id, player_id=player_id)
        await self.redis.set(key, vote_var)

    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        key = self._create_key(team_id=team_id, player_id=player_id)
        await self.redis.delete(key)

    async def get_dict_player_vote(self, team_id: int) -> dict[int, Played]:
        """

        :param team_id:
        :return: словарь в формате player_id:vote
        """
        return {
            self.parse_player_id(key=key, team_id=team_id): Played[await self._get(key)]
            for key in await self.get_list_of_keys_pool(team_id=team_id)
        }

    async def save_pool_msg_id(self, chat_id: int, game_id: int, msg_id: int) -> None:
        key = self._create_msg_prefix(chat_id, game_id)
        await self.redis.set(key, msg_id)

    async def get_pool_msg_id(self, chat_id: int, game_id: int) -> int | None:
        key = self._create_msg_prefix(chat_id, game_id)
        msg_id = await self._get(key)
        return None if msg_id is None else int(msg_id)

    def _create_key(self, team_id: int, player_id: int) -> str:
        return f"{self.prefix}:{team_id}:{player_id}"

    def _create_msg_prefix(self, chat_id: int, game_id: int) -> str:
        return f"{self.msg_prefix}:{chat_id}:{game_id}"

    async def get_list_of_keys_pool(self, team_id: int) -> list[str]:
        """

        :param team_id:
        :return: список ключей для команды team_id в формате prefix:team_id:player_id
        """
        rez = await self.redis.keys(f"{self.prefix}:{team_id}:*", encoding="utf-8")
        return rez

    def parse_player_id(self, key: str, team_id: int) -> int:
        """

        :param key: ключ в формате prefix:team_id:player_id
        :param team_id:
        :return: player_id
        """
        player_id = key[len(f"{self.prefix}:{team_id}:") :]
        return int(player_id)

    async def delete_all(self) -> None:
        keys: list = await self.redis.keys(f"{self.prefix}:*")
        keys.extend(await self.redis.keys(f"{self.msg_prefix}:*"))
        if len(keys) == 0:
            return logger.warning("pool-keys to delete not found")
        logger.warning("Next keys was deleted %s", ", ".join([key.decode() for key in keys]))
        await self.redis.delete(*keys)

    async def _get(self, key: str, encoding: str = "utf-8"):
        value = await self.redis.get(key)
        if value is None:
            return None
        return value.decode(encoding)
