from dataclasses import dataclass
from typing import Iterable

from db.dao import PollDao, WaiverDao, OrganizerDao
from shvatka.dal.game_play import GamePreparer
from shvatka.models import dto


@dataclass
class GamePreparerImpl(GamePreparer):
    poll: PollDao
    waiver: WaiverDao
    org: OrganizerDao

    async def delete_poll_data(self) -> None:
        return await self.poll.delete_all()

    async def get_agree_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        return await self.waiver.get_agree_teams(game)

    async def get_orgs(self, game: dto.Game) -> Iterable[dto.Organizer]:
        return await self.org.get_orgs(game)
