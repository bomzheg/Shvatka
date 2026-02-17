from typing import TypedDict

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.models import dto
from shvatka.infrastructure.db.dao import GameDao


class LoadedData(TypedDict, total=False):
    game: dto.Game | None
    full_game: dto.FullGame | None


class CurrentGameProviderImpl(CurrentGameProvider):
    def __init__(
        self,
        *,
        dao: GameDao,
    ) -> None:
        self.dao = dao
        self.cache = LoadedData()

    async def get_game(self) -> dto.Game | None:
        if "game" in self.cache:
            return self.cache["game"]
        game = await self.dao.get_active_game()

        self.cache["game"] = game
        return game

    async def get_full_game(self) -> dto.FullGame | None:
        if "full_game" in self.cache:
            return self.cache["full_game"]
        game = await self.get_game()
        if game is None:
            self.cache["full_game"] = None
            return None
        full_game = await self.dao.get_full(game.id)
        self.cache["full_game"] = full_game
        return full_game
