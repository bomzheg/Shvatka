from typing import Callable, Any, Awaitable

from adaptix import Retort
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram_dialog.api.protocols import BgManagerFactory
from dataclass_factory import Factory

from shvatka.core.interfaces.clients.file_storage import FileStorage, FileGateway
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import GameLogWriter
from shvatka.core.views.level import LevelView
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.picture.results_painter import ResultsPainter
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.utils.data import MiddlewareData
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.telegraph import Telegraph


class InitMiddleware(BaseMiddleware):
    def __init__(
        self,
        bg_manager_factory: BgManagerFactory,
    ) -> None:
        self.bg_manager_factory = bg_manager_factory

    async def __call__(  # type: ignore[override]
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        dishka = data["dishka_container"]
        file_storage = await dishka.get(FileStorage)  # type: ignore[type-abstract]
        data["config"] = await dishka.get(BotConfig)
        data["main_config"] = await dishka.get(TgBotConfig)
        data["user_getter"] = await dishka.get(UserGetter)
        data["dcf"] = await dishka.get(Factory)
        data["retort"] = await dishka.get(Retort)
        data["scheduler"] = await dishka.get(Scheduler)  # type: ignore[type-abstract]
        data["locker"] = await dishka.get(KeyCheckerFactory)  # type: ignore[type-abstract]
        data["file_storage"] = file_storage
        data["telegraph"] = await dishka.get(Telegraph)
        data["bg_manager_factory"] = self.bg_manager_factory
        data["game_log"] = await dishka.get(GameLogWriter)  # type: ignore[type-abstract]
        data["file_gateway"] = await dishka.get(FileGateway)  # type: ignore[type-abstract]
        data["hint_sender"] = await dishka.get(HintSender)
        data["level_view"] = await dishka.get(LevelView)  # type: ignore[type-abstract]
        holder_dao = await dishka.get(HolderDao)
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
