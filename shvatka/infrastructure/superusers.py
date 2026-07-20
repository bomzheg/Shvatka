from dataclasses import dataclass

from shvatka.common import Config
from shvatka.core.notifications.adapters import SuperusersResolver
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao import PlayerDao


@dataclass
class ConfigSuperusersResolver(SuperusersResolver):
    """Maps the configured superuser tg ids onto player ids, skipping unknown ones."""

    config: Config
    player_dao: PlayerDao

    async def get_superuser_player_ids(self) -> set[int]:
        player_ids = set()
        for tg_id in self.config.superusers:
            try:
                player = await self.player_dao.get_by_user_id(tg_id)
            except exceptions.PlayerNotFoundError:
                continue
            player_ids.add(player.id)
        return player_ids
