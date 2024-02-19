from dishka import Provider, provide, Scope

from shvatka.core.services.game import get_active
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.core.models import dto


class GameProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_game(self, dao: HolderDao) -> dto.Game | None:
        return await get_active(dao.game)
