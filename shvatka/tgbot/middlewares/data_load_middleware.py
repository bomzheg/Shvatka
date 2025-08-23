from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.tgbot.services.identity import TgBotIdentityProvider
from shvatka.tgbot.utils.data import SHMiddlewareData


class LoadDataMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: SHMiddlewareData,
    ) -> Any:
        dishka = data["dishka_container"]
        identity_provider = await dishka.get(TgBotIdentityProvider)
        current_game = await dishka.get(CurrentGameProvider)

        data["user"] = await identity_provider.get_user()
        data["chat"] = await identity_provider.get_chat()
        data["player"] = await identity_provider.get_player()
        data["team"] = await identity_provider.get_team()

        data["game"] = await current_game.get_game()
        result = await handler(event, data)  # type: ignore[arg-type]
        return result
