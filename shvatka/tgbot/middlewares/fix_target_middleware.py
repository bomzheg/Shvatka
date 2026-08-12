from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from dishka.integrations.aiogram import CONTAINER_NAME

from shvatka.core.players.player import upsert_player
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.username_resolver.find_target_user import get_db_user_by_tg_user
from shvatka.tgbot.username_resolver.user_getter import UserGetter


class FixTargetMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if target := data.get("target"):
            container = data[CONTAINER_NAME]
            dao = await container.get(HolderDao)
            user_getter = await container.get(UserGetter)
            target = await get_db_user_by_tg_user(target, user_getter, dao)
            data["target"] = await upsert_player(target, dao.player)
        return await handler(event, data)
