from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram_dialog.api.protocols import BgManagerFactory
from dataclass_factory import Factory
from dishka import AsyncContainer

from shvatka.core.interfaces.clients.file_storage import FileStorage, FileGateway
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.picture.results_painter import ResultsPainter
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.utils.data import MiddlewareData
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from shvatka.tgbot.views.telegraph import Telegraph


class InitMiddleware(BaseMiddleware):
    def __init__(
        self,
        dishka: AsyncContainer,
        bg_manager_factory: BgManagerFactory,
    ) -> None:
        self.dishka = dishka
        self.bg_manager_factory = bg_manager_factory

    async def __call__(  # type: ignore[override]
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        file_storage = await self.dishka.get(FileStorage)  # type: ignore[type-abstract]
        data["config"] = await self.dishka.get(BotConfig)
        data["main_config"] = await self.dishka.get(TgBotConfig)
        data["user_getter"] = await self.dishka.get(UserGetter)
        data["dcf"] = await self.dishka.get(Factory)
        data["scheduler"] = await self.dishka.get(Scheduler)  # type: ignore[type-abstract]
        data["locker"] = await self.dishka.get(KeyCheckerFactory)  # type: ignore[type-abstract]
        data["file_storage"] = file_storage
        data["telegraph"] = await self.dishka.get(Telegraph)
        data["bg_manager_factory"] = self.bg_manager_factory
        data["game_log"] = await self.dishka.get(GameLogWriter)
        async with self.dishka() as request_dishka:
            data["file_gateway"] = await request_dishka.get(FileGateway)  # type: ignore[type-abstract]
            holder_dao = await request_dishka.get(HolderDao)
            data["dao"] = holder_dao
            data["hint_parser"] = HintParser(
                dao=holder_dao.file_info,
                file_storage=file_storage,
                bot=data["bot"],
            )
            data["results_painter"] = ResultsPainter(
                data["bot"],
                holder_dao,
                data["config"].log_chat,
            )
            result = await handler(event, data)
        return result
