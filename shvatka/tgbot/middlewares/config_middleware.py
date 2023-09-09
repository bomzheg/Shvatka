from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.utils.data import MiddlewareData


class ConfigMiddleware(BaseMiddleware):
    def __init__(self, config: BotConfig) -> None:
        self.config = config

    async def __call__(  # type: ignore
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        data["config"] = self.config
        return await handler(event, data)
