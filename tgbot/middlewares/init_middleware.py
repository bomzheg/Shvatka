from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from dataclass_factory import Factory
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from infrastructure.clients.file_gateway import BotFileGateway
from infrastructure.db.dao.holder import HolderDao
from infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.interfaces.clients.file_storage import FileStorage
from shvatka.interfaces.scheduler import Scheduler
from shvatka.utils.key_checker_lock import KeyCheckerFactory
from tgbot.username_resolver.user_getter import UserGetter
from tgbot.views.hint_factory.hint_parser import HintParser
from tgbot.views.telegraph import Telegraph


class InitMiddleware(BaseMiddleware):
    def __init__(
        self,
        pool: sessionmaker,
        user_getter: UserGetter,
        dcf: Factory,
        redis: Redis,
        scheduler: Scheduler,
        locker: KeyCheckerFactory,
        file_storage: FileStorage,
        level_test_dao: LevelTestingData,
        telegraph: Telegraph,
    ):
        self.pool = pool
        self.user_getter = user_getter
        self.dcf = dcf
        self.redis = redis
        self.scheduler = scheduler
        self.locker = locker
        self.file_storage = file_storage
        self.level_test_dao = level_test_dao
        self.telegraph = telegraph

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["user_getter"] = self.user_getter
        data["dcf"] = self.dcf
        data["scheduler"] = self.scheduler
        data["locker"] = self.locker
        data["file_storage"] = self.file_storage
        data["telegraph"] = self.telegraph
        async with self.pool() as session:
            holder_dao = HolderDao(session, self.redis, self.level_test_dao)
            data["dao"] = holder_dao
            data["hint_parser"] = HintParser(
                dao=holder_dao.file_info,
                file_storage=self.file_storage,
                bot=data["bot"],
            )
            data["file_gateway"] = BotFileGateway(
                bot=data["bot"], file_storage=self.file_storage, hint_parser=data["hint_parser"]
            )
            result = await handler(event, data)
            del data["dao"]
        return result
