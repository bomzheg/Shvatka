from dataclasses import dataclass

from aiogram.filters import BaseFilter
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.current_game import CurrentGameProvider


@dataclass
class SentAfterGameStartFilter(BaseFilter):
    @inject
    async def __call__(
        self, message: Message, current_game: FromDishka[CurrentGameProvider]
    ) -> bool:
        game = await current_game.get_game()
        if game is None or game.start_at is None:
            return False
        return message.date > game.start_at
