from dataclasses import dataclass
from typing import Iterable

from db.dao import PollDao, WaiverDao, OrganizerDao, GameDao, LevelTimeDao, LevelDao, KeyTimeDao
from shvatka.dal.game_play import GamePreparer, GamePlayerDao
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


@dataclass
class GamePlayerDaoImpl(GamePlayerDao):
    level_time: LevelTimeDao
    level: LevelDao
    key_time: KeyTimeDao
    waiver: WaiverDao
    game: GameDao

    async def is_team_finished(self, team: dto.Team, game: dto.FullGame) -> bool:
        level_number = await self.level_time.get_current_level(team, game.id)
        return level_number == len(game.levels)

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        return await self.waiver.get_played_teams(game)

    async def is_all_team_finished(self, game: dto.FullGame) -> bool:
        for team in await self.get_played_teams(game):
            if not await self.is_team_finished(team, game):
                return False
        return True

    async def is_key_duplicate(self, level: dto.Level, team: dto.Team, key: str) -> bool:
        return await self.key_time.is_duplicate(level, team, key)

    async def get_current_level(self, team: dto.Team, game: dto.Game) -> dto.Level:
        return await self.level.get_by_number(
            game=game,
            level_number=await self.level_time.get_current_level(team=team, game_id=game.id)
        )

    async def get_correct_typed_keys(
        self, level: dto.Level, game: dto.Game, team: dto.Team,
    ) -> set[str]:
        return await self.key_time.get_correct_typed_keys(level, game, team)

    async def save_key(
        self, key: str, team: dto.Team, level: dto.Level, game: dto.Game,
        player: dto.Player, is_correct: bool, is_duplicate: bool,
    ) -> dto.KeyTime:
        return await self.key_time.save_key(
            key=key, team=team, level=level, game=game, player=player,
            is_correct=is_correct, is_duplicate=is_duplicate,
        )

    async def level_up(self, team: dto.Team, level: dto.Level, game: dto.Game) -> None:
        await self.level_time.set_to_level(
            team=team, game=game, level_number=level.number_in_game + 1,
        )

    async def finish(self, game: dto.Game) -> None:
        await self.game.set_finished(game)

    async def commit(self) -> None:
        await self.key_time.commit()
