from dishka import Provider, Scope, provide

from shvatka.core.models import dto
from shvatka.core.services.player import upsert_player
from shvatka.infrastructure.db.dao.holder import HolderDao


class PlayerProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def db_player_provider(self, dao: HolderDao, user: dto.User) -> dto.Player:
        return await upsert_player(user, dao.player)
