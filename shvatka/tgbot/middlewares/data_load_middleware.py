from typing import Any
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from shvatka.tgbot.services.identity import TgBotIdentityProvider
from shvatka.tgbot.utils.data import SHMiddlewareData


class LoadDataMiddleware(BaseMiddleware):
    """
    Keeps the acting user, chat and player in sync with what Telegram just sent.

    Resolving them is a write: ``get_user`` and ``get_chat`` upsert the row for
    every update (so a renamed user or chat is never stale), and ``get_player``
    creates the player of a user who is here for the first time. Handlers ask
    for the same values through ``IdentityProvider``, which is request-scoped
    and caches them, so priming it here costs nothing beyond those upserts.
    """

    async def __call__(  # type: ignore[override]
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: SHMiddlewareData,
    ) -> Any:
        dishka = data["dishka_container"]
        identity_provider = await dishka.get(TgBotIdentityProvider)

        await identity_provider.get_chat()
        # loads (and so upserts) the user on the way to the player
        await identity_provider.get_player()

        return await handler(event, data)  # type: ignore[arg-type]
