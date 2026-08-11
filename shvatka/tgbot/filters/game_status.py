from dataclasses import dataclass
from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus


@dataclass
class GameStatusFilter(BaseFilter):
    active: bool | None = None
    running: bool | None = None
    status: GameStatus | None = None

    @inject
    async def __call__(
        self, message: Message, current_game: FromDishka[CurrentGameProvider]
    ) -> bool | dict[str, Any]:
        game = await current_game.get_game()
        if self.active is not None:
            return self.check_active(game)
        if self.running is not None:
            return self.check_running(game)
        if self.status is not None:
            return self.check_by_status(game)
        return True

    def check_active(self, game: dto.Game | None) -> bool:
        if game is not None and game.is_active():
            return bool(self.active)
        return not self.active

    def check_running(self, game: dto.Game | None) -> bool:
        if game is not None and game.is_started():
            return bool(self.running)
        return not self.running

    def check_by_status(self, game: dto.Game | None) -> bool:
        if game is None:
            return False
        return game.status == self.status
