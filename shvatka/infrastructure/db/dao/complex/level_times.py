import typing
from dataclasses import dataclass

from shvatka.core.games.adapters import GameStatReader
from shvatka.core.interfaces.dal.complex import GameStatDao
from shvatka.core.models import dto

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class GameStatImpl(GameStatDao):
    dao: "HolderDao"

    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        return await self.dao.level_time.get_game_level_times(game)

    async def get_max_level_number(self, game: dto.Game) -> int:
        return await self.dao.level.get_max_level_number(game)

    async def get_by_player(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return await self.dao.organizer.get_by_player(game=game, player=player)

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        return await self.dao.organizer.get_by_player_or_none(game=game, player=player)

    async def get_game_level_times_by_teams(
        self, game: dto.Game
    ) -> dict[dto.Team, list[dto.LevelTime]]:
        return await self.dao.level_time.get_game_level_times_by_teams(game)

    async def get_game_level_times_with_hints(
        self, game: dto.FullGame
    ) -> dict[dto.Team, list[dto.LevelTimeOnGame]]:
        return await self.dao.level_time.get_game_level_times_with_hints(game)

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_, author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        return await self.dao.game.add_levels(game)


class GameStatReaderImpl(GameStatReader):
    def __init__(self, dao: "HolderDao"):
        self.dao = dao

    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        return await self.dao.level_time.get_game_level_times(game)

    async def get_max_level_number(self, game: dto.Game) -> int:
        return await self.dao.level.get_max_level_number(game)

    async def get_by_player(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return await self.dao.organizer.get_by_player(game=game, player=player)

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        return await self.dao.organizer.get_by_player_or_none(game=game, player=player)

    async def get_game_level_times_by_teams(
        self, game: dto.Game
    ) -> dict[dto.Team, list[dto.LevelTime]]:
        return await self.dao.level_time.get_game_level_times_by_teams(game)

    async def get_game_level_times_with_hints(
        self, game: dto.FullGame
    ) -> dict[dto.Team, list[dto.LevelTimeOnGame]]:
        return await self.dao.level_time.get_game_level_times_with_hints(game)

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_, author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        return await self.dao.game.add_levels(game)

    async def get_by_user(self, user: dto.User) -> dto.Player:
        return await self.dao.player.get_by_user(user)
