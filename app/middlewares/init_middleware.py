from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from dataclass_factory import Factory
from sqlalchemy.orm import sessionmaker

from app.dao.holder import HolderDao
from app.services.username_resolver.user_getter import UserGetter


class InitMiddleware(BaseMiddleware):
    def __init__(self, pool: sessionmaker, user_getter: UserGetter, dcf: Factory):
        self.pool = pool
        self.user_getter = user_getter
        self.dcf = dcf

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        data["user_getter"] = self.user_getter
        data["dcf"] = self.dcf
        async with self.pool() as session:
            holder_dao = HolderDao(session)
            data["dao"] = holder_dao
            result = await handler(event, data)
            del data["dao"]
        return result
