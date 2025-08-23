from typing import Protocol

from shvatka.core.models import dto
from shvatka.core.utils import exceptions


class CurrentGameProvider(Protocol):
    async def get_game(self) -> dto.Game | None:
        raise NotImplementedError

    async def get_required_game(self) -> dto.Game:
        game = await self.get_game()
        if game is None:
            raise exceptions.HaveNotActiveGame
        return game
