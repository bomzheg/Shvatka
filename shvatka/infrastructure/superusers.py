from dataclasses import dataclass

from shvatka.common import Config
from shvatka.core.interfaces.superusers import SuperusersResolver
from shvatka.core.models import dto
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao import PlayerDao


@dataclass
class ConfigSuperusersResolver(SuperusersResolver):
    """Reads the configured superuser tg ids and exposes them as the single
    source of admin rights (as tg ids, as player ids, and as a membership check)."""

    config: Config
    player_dao: PlayerDao

    def is_superuser(self, user: dto.User) -> bool:
        return user.tg_id in self.config.superusers

    async def get_superuser_user_ids(self) -> set[int]:
        return set(self.config.superusers)

    async def get_superuser_player_ids(self) -> set[int]:
        player_ids = set()
        for tg_id in self.config.superusers:
            try:
                player = await self.player_dao.get_by_user_id(tg_id)
            except exceptions.PlayerNotFoundError:
                continue
            player_ids.add(player.id)
        return player_ids
