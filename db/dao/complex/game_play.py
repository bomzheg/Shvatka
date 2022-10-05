from dataclasses import dataclass
from typing import Iterable

from db.dao import PollDao, WaiverDao, OrganizerDao, GameDao, LevelTimeDao, LevelDao
from shvatka.dal.game_play import GamePreparer
from shvatka.dal.level_times import GameStarter
from shvatka.models import dto
from shvatka.models.dto.scn.time_hint import TimeHint


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

    async def get_next_hint(self, game: dto.Game, current_level: int, current_hint: int) -> TimeHint:
        scenario = await self.level.get_scenario(game, current_level)
        return scenario.time_hints[current_hint + 1]

    async def get_puzzle(self, game: dto.Game, level_number: int) -> TimeHint:
        scenario = await self.level.get_scenario(game, level_number)
        return scenario.time_hints[0]

    async def commit(self) -> None:
        await self.game.commit()
