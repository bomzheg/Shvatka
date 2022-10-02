from typing import Iterable

from shvatka.dal.base import Writer
from shvatka.models import dto


class GamePreparer(Writer):
    async def delete_poll_data(self) -> None: pass

    async def get_agree_teams(self, game: dto.Game) -> Iterable[dto.Team]: pass

    async def get_orgs(self, game: dto.Game) -> Iterable[dto.Organizer]: pass
