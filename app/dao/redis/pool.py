import logging

from redis.asyncio.client import Redis  # noqa

from app.models.enums.played import Played

logger = logging.getLogger(__name__)


class PollDao:
    def __init__(self, redis: Redis):
        self.prefix = "poll"
        self.msg_prefix = "msg_poll"
        self.redis = redis

    async def get_dict_vote_player(self, team_id: int) -> dict[Played, list[int]]:
        """
        :param team_id:
        :return: словарь в формате vote:[player_id1, player_id2, ...]
        """
        in_dict = await self.get_dict_player_vote(team_id)
        out_dict = dict()
        for player_id, vote in in_dict.items():
            out_dict.setdefault(vote, []).append(player_id)
        return out_dict

    async def get_list_player_with_vote(self, team_id: int, vote: str) -> list[int]:
        keys = await self.get_list_of_keys_pool(team_id=team_id)
        rez_list = []
        for key in keys:
            if vote == await self.redis.get(key, encoding='utf-8'):
                rez_list.append(
                    self.parse_player_id(key=key, team_id=team_id)
                )
        return rez_list

    async def get_player_vote(self, team_id: int, player_id: int) -> str:
        key = self._create_key(team_id=team_id, player_id=player_id)
        return await self.redis.get(key, encoding='utf-8')

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
            self.parse_player_id(
                key=key,
                team_id=team_id
            ): Played[await self.redis.get(key, encoding='utf-8')]
            for key in await self.get_list_of_keys_pool(team_id=team_id)
        }

    async def save_pool_msg_id(self, chat_id: int, game_id: int, msg_id: int) -> None:
        key = self._create_msg_prefix(chat_id, game_id)
        await self.redis.set(key, msg_id)

    async def get_pool_msg_id(self, chat_id: int, game_id: int) -> int | None:
        key = self._create_msg_prefix(chat_id, game_id)
        msg_id = await self.redis.get(key, encoding='utf-8')
        return None if msg_id is None else int(msg_id)

    async def get_voted_team_ids(self) -> set[int]:
        """TODO unused?"""
        keys = await self.redis.keys(f'{self.prefix}:*', encoding='utf-8')
        return {self.parse_team_id(key) for key in keys}

    def _create_key(self, team_id: int, player_id: int) -> str:
        return f"{self.prefix}:{team_id}:{player_id}"

    def _create_msg_prefix(self, chat_id: int, game_id: int) -> str:
        return f"{self.msg_prefix}:{chat_id}:{game_id}"

    def parse_team_id(self, key: str) -> int:
        current_prefix = key.split(':')[0]
        if current_prefix != self.prefix:
            raise ValueError(f"prefix of key is {current_prefix} but must be {self.prefix}")
        return int(key.split(':')[1])

    async def get_list_of_keys_pool(self, team_id: int) -> list[str]:
        """

        :param team_id:
        :return: список ключей для команды team_id в формате prefix:team_id:player_id
        """
        rez = await self.redis.keys(f"{self.prefix}:{team_id}:*", encoding='utf-8')
        return rez

    def parse_player_id(self, key: str, team_id: int) -> int:
        """

        :param key: ключ в формате prefix:team_id:player_id
        :param team_id:
        :return: player_id
        """
        player_id = key[len(f"{self.prefix}:{team_id}:"):]
        return int(player_id)

    async def remove_all_poll_data(self) -> None:
        keys: list = await self.redis.keys(f'{self.prefix}:*')
        keys.extend(await self.redis.keys(f'{self.msg_prefix}:*'))
        if len(keys) == 0:
            return logger.warning("pool-keys to delete not found")
        logger.warning("Next keys was deleted %s", ", ".join([key.decode() for key in keys]))
        await self.redis.delete(*keys)
