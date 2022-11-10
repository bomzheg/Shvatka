from shvatka.dal.base import Reader
from shvatka.models import dto


class GameOrgsGetter(Reader):
    async def get_orgs(self, game: dto.Game) -> list[dto.Organizer]:
        raise NotImplementedError
