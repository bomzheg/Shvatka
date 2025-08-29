from typing import TypedDict

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.models import dto
from shvatka.infrastructure.db.dao import GameDao


class LoadedData(TypedDict, total=False):
    game: dto.Game | None


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
