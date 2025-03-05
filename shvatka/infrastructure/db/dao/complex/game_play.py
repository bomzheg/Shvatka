import typing
from dataclasses import dataclass
from typing import Iterable


from shvatka.core.interfaces.dal.game_play import GamePreparer, GamePlayerDao
from shvatka.core.interfaces.dal.level_times import GameStarter
from shvatka.core.models import dto, enums

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class GamePreparerImpl(GamePreparer):
    dao: "HolderDao"

    async def delete_poll_data(self) -> None:
        return await self.dao.poll.delete_all()

    async def get_agree_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        return await self.dao.waiver.get_played_teams(game)

    async def get_orgs(
        self, game: dto.Game, with_deleted: bool = False
    ) -> list[dto.SecondaryOrganizer]:
        return await self.dao.organizer.get_orgs(game)

    async def get_poll_msg(self, team: dto.Team, game: dto.Game) -> int | None:
        chat_id = team.get_chat_id()
        assert chat_id is not None
        return await self.dao.poll.get_poll_msg_id(chat_id=chat_id, game_id=game.id)


@dataclass
class GameStarterImpl(GameStarter):
    dao: "HolderDao"

    async def set_game_started(self, game: dto.Game) -> None:
        return await self.dao.game.set_started(game)

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        return await self.dao.waiver.get_played_teams(game)

    async def set_to_level(
        self,
        team: dto.Team,
        game: dto.Game,
        level_number: int,
    ) -> dto.LevelTime:
        return await self.dao.level_time.set_to_level(
            team=team, game=game, level_number=level_number
        )

    async def commit(self) -> None:
        await self.dao.commit()


@dataclass
class GamePlayerDaoImpl(GamePlayerDao):
    dao: "HolderDao"

    async def check_waiver(self, player: dto.Player, team: dto.Team, game: dto.Game) -> bool:
        return await self.dao.waiver.check_waiver(player, team, game)

    async def is_team_finished(self, team: dto.Team, game: dto.FullGame) -> bool:
        level_number = await self.dao.level_time.get_current_level(team, game)
        return level_number == len(game.levels)

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        return await self.dao.waiver.get_played_teams(game)

    async def is_all_team_finished(self, game: dto.FullGame) -> bool:
        for team in await self.get_played_teams(game):
            if not await self.is_team_finished(team, game):
                return False
        return True

    async def is_key_duplicate(self, level: dto.LevelTime, team: dto.Team, key: str) -> bool:
        return await self.dao.key_time.is_duplicate(level, team, key)

    async def get_current_level(self, team: dto.Team, game: dto.Game) -> dto.Level:
        return await self.dao.level.get_by_number(
            game=game,
            level_number=await self.dao.level_time.get_current_level(team=team, game=game),
        )

    async def get_correct_typed_keys(
        self,
        level_time: dto.LevelTime,
        game: dto.Game,
        team: dto.Team,
    ) -> set[str]:
        return await self.dao.key_time.get_correct_typed_keys(level_time, game, team)

    async def save_key(
        self,
        key: str,
        team: dto.Team,
        level_time: dto.LevelTime,
        game: dto.Game,
        player: dto.Player,
        type_: enums.KeyType,
        is_duplicate: bool,
    ) -> dto.KeyTime:
        return await self.dao.key_time.save_key(
            key=key,
            team=team,
            level_time=level_time,
            game=game,
            player=player,
            type_=type_,
            is_duplicate=is_duplicate,
        )

    async def get_team_typed_keys(
        self, game: dto.Game, team: dto.Team, level_time: dto.LevelTime
    ) -> list[dto.KeyTime]:
        return await self.dao.key_time.get_team_typed_keys(game, team, level_time)

    async def level_up(
        self, team: dto.Team, level: dto.Level, game: dto.Game, next_level_number: int
    ) -> None:
        await self.dao.level_time.set_to_level(
            team=team,
            game=game,
            level_number=next_level_number,
        )

    async def finish(self, game: dto.Game) -> None:
        await self.dao.game.set_finished(game)

    async def get_current_level_time(self, team: dto.Team, game: dto.Game) -> dto.LevelTime:
        return await self.dao.level_time.get_current_level_time(team=team, game=game)

    async def get_orgs(
        self, game: dto.Game, with_deleted: bool = False
    ) -> list[dto.SecondaryOrganizer]:
        return await self.dao.organizer.get_orgs(game)

    async def get_next_level(self, level: dto.Level, game: dto.Game) -> dto.Level:
        assert level.number_in_game is not None
        return await self.dao.level.get_by_number(game=game, level_number=level.number_in_game + 1)

    async def get_level_by_name(self, level_name: str, game: dto.Game) -> dto.Level | None:
        return await self.dao.level.get_by_author_and_name_id(game.author, level_name)

    async def commit(self) -> None:
        await self.dao.commit()
