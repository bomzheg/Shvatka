from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from dataclass_factory import Factory
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.picture.results_painter import ResultsPainter
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.utils.data import MiddlewareData
from shvatka.tgbot.views.game import GameBotLog
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from shvatka.tgbot.views.telegraph import Telegraph


class InitMiddleware(BaseMiddleware):
    def __init__(
        self,
        pool: async_sessionmaker[AsyncSession],
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

    async def __call__(  # type: ignore[override]
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        data["user_getter"] = self.user_getter
        data["dcf"] = self.dcf
        data["scheduler"] = self.scheduler
        data["locker"] = self.locker
        data["file_storage"] = self.file_storage
        data["telegraph"] = self.telegraph
        data["game_log"] = GameBotLog(bot=data["bot"], log_chat_id=data["config"].log_chat)
        async with self.pool() as session:
            holder_dao = HolderDao(session, self.redis, self.level_test_dao)
            data["dao"] = holder_dao
            data["hint_parser"] = HintParser(
                dao=holder_dao.file_info,
                file_storage=self.file_storage,
                bot=data["bot"],
            )
            data["file_gateway"] = BotFileGateway(
                bot=data["bot"],
                file_storage=self.file_storage,
                hint_parser=data["hint_parser"],
                tech_chat_id=data["config"].log_chat,
            )
            data["results_painter"] = ResultsPainter(
                data["bot"],
                holder_dao,
                data["config"].log_chat,
            )
            result = await handler(event, data)
            del data["dao"]
        return result
