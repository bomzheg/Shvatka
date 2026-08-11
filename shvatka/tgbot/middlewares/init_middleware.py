from typing import Callable, Any, Awaitable

from adaptix import Retort
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.utils.data import SHMiddlewareData


class InitMiddleware(BaseMiddleware):
    """
    Puts into middleware data only what handlers ask for by name too often to
    be worth an explicit ``FromDishka``. Everything else is resolved lazily by
    the handler that needs it, so an update doesn't pay for objects it ignores.
    """

    async def __call__(  # type: ignore[override]
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: SHMiddlewareData,
    ) -> Any:
        dishka = data["dishka_container"]
        data["dao"] = await dishka.get(HolderDao)
        data["retort"] = await dishka.get(Retort)
        result = await handler(event, data)  # type: ignore[arg-type]
        return result
