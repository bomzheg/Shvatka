from dataclasses import dataclass
from typing import Iterable

from db.dao import PollDao, WaiverDao, OrganizerDao, GameDao, LevelTimeDao, LevelDao
from shvatka.dal.game_play import GamePreparer
from shvatka.dal.level_times import GameStarter
from shvatka.models import dto


@dataclass
class GamePreparerImpl(GamePreparer):
    poll: PollDao
    waiver: WaiverDao
    org: OrganizerDao

    async def delete_poll_data(self) -> None:
        return await self.poll.delete_all()

    async def get_agree_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        return await self.waiver.get_played_teams(game)

    async def get_orgs(self, game: dto.Game) -> Iterable[dto.Organizer]:
        return await self.org.get_orgs(game)


@dataclass
class GameStarterImpl(GameStarter):
    game: GameDao
    waiver: WaiverDao
    level_times: LevelTimeDao
    level: LevelDao

    async def set_game_started(self, game: dto.Game) -> None:
        return await self.game.set_started(game)

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        return await self.waiver.get_played_teams(game)

    async def set_teams_to_first_level(self, game: dto.Game, teams: Iterable[dto.Team]) -> None:
        for team in teams:
            await self.level_times.set_to_level(team=team, game=game, level_number=0)

    async def commit(self) -> None:
        await self.game.commit()
