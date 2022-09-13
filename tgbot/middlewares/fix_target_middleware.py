from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.dao.holder import HolderDao
from app.services.player import upsert_player
from app.services.username_resolver.find_target_user import get_db_user_by_tg_user


class FixTargetMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        if target := data.get("target", None):
            dao: HolderDao = data["dao"]
            target = await get_db_user_by_tg_user(target, data["user_getter"], dao)
            data["target"] = await upsert_player(target, dao.player)
        return await handler(event, data)
