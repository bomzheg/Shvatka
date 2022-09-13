from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.models.config.main import BotConfig


class ConfigMiddleware(BaseMiddleware):
    def __init__(self, config: BotConfig):
        self.config = config

    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> Any:
        data["config"] = self.config
        return await handler(event, data)
