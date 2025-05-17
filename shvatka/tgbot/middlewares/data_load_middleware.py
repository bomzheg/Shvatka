from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from shvatka.core.services.game import get_active
from shvatka.infrastructure.db.dao.holder import HolderDao
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
        data["user"] = await identity_provider.get_user()
        data["chat"] = await identity_provider.get_chat()
        data["player"] = await identity_provider.get_player()
        data["team"] = await identity_provider.get_team()

        dao = await dishka.get(HolderDao)
        data["game"] = await get_active(dao.game)
        result = await handler(event, data)  # type: ignore[arg-type]
        return result
