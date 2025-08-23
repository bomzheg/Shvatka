from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from shvatka.tgbot.services.identity import TgBotIdentityProvider
from shvatka.tgbot.utils.data import SHMiddlewareData


class TeamPlayerMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore[override]
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: SHMiddlewareData,
    ) -> Any:
        dishka = data["dishka_container"]
        identity_provider = await dishka.get(TgBotIdentityProvider)
        data["team_player"] = await identity_provider.get_full_team_player()
        result = await handler(event, data)  # type: ignore[arg-type]
        return result
