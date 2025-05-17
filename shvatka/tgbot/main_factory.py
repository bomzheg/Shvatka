import logging
from typing import AsyncIterable

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.base import BaseStorage, BaseEventIsolation
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder, RedisEventIsolation
from aiogram.types import TelegramObject
from aiogram_dialog.api.protocols import MessageManagerProtocol
from aiogram_dialog.manager.message_manager import MessageManager
from dishka import (
    AsyncContainer,
    make_async_container,
    Provider,
    Scope,
    provide,
    AnyOf,
    STRICT_VALIDATION, from_context,
)
from dishka.integrations.aiogram import setup_dishka, AiogramMiddlewareData
from redis.asyncio import Redis

from shvatka.common.factory import TelegraphProvider, DCFProvider, UrlProvider
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import GameLogWriter, GameView, GameViewPreparer, OrgNotifier
from shvatka.core.views.level import LevelView
from shvatka.infrastructure.db.config.models.storage import StorageConfig, StorageType
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.factory import (
    create_redis,
    create_lock_factory,
)
from shvatka.infrastructure.di import get_providers
from shvatka.infrastructure.picture import ResultsPainter
from shvatka.infrastructure.scheduler.factory import SchedulerProvider
from shvatka.tgbot.config.models.bot import BotConfig, TgClientConfig
from shvatka.tgbot.handlers import setup_handlers
from shvatka.tgbot.middlewares import setup_middlewares
from shvatka.tgbot.services.identity import TgBotIdentityProvider
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.utils.router import print_router_tree
from shvatka.tgbot.views.game import GameBotLog, BotView, BotOrgNotifier
from shvatka.tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.level_testing import LevelBotView

logger = logging.getLogger(__name__)


def create_dishka(paths_env: str) -> AsyncContainer:
    container = make_async_container(
        *get_bot_providers(paths_env), validation_settings=STRICT_VALIDATION
    )
    return container


def get_bot_providers(paths_env: str) -> list[Provider]:
    return [
        *get_providers(paths_env),
        *get_bot_specific_providers(),
        *get_bot_only_providers(),
    ]


def get_bot_specific_providers() -> list[Provider]:
    return [
        DpProvider(),
        DialogManagerProvider(),
        SchedulerProvider(),
        TelegraphProvider(),
        DCFProvider(),
        GameToolsProvider(),
        UserGetterProvider(),
        LockProvider(),
        UrlProvider(),
        BotIdpProvider(),
    ]


def get_bot_only_providers() -> list[Provider]:
    return [
        BotOnlyIdpProvider(),
    ]


class DialogManagerProvider(Provider):
    scope = Scope.APP

    @provide
    def get_manager(self) -> MessageManagerProtocol:
        return MessageManager()


class LockProvider(Provider):
    scope = Scope.APP

    @provide
    def get_lock_factory(self) -> KeyCheckerFactory:
        return create_lock_factory()


class DpProvider(Provider):
    scope = Scope.APP

    @provide
    def create_dispatcher(
        self,
        dishka: AsyncContainer,
        event_isolation: BaseEventIsolation,
        bot_config: BotConfig,
        storage: BaseStorage,
        message_manager: MessageManagerProtocol,
    ) -> Dispatcher:
        dp = Dispatcher(
            storage=storage,
            events_isolation=event_isolation,
        )
        setup_dishka(container=dishka, router=dp)
        bg_manager_factory = setup_handlers(dp, bot_config, message_manager)
        setup_middlewares(
            dp=dp,
            bg_manager_factory=bg_manager_factory,
        )
        logger.info("Configured bot routers \n%s", print_router_tree(dp))
        return dp

    @provide
    def create_storage(self, config: StorageConfig) -> BaseStorage:
        logger.info("creating storage for type %s", config.type_)
        match config.type_:
            case StorageType.memory:
                return MemoryStorage()
            case StorageType.redis:
                if config.redis is None:
                    raise ValueError("you have to specify redis config for use redis storage")
                return RedisStorage(
                    create_redis(config.redis), key_builder=DefaultKeyBuilder(with_destiny=True)
                )
            case _:
                raise NotImplementedError

    @provide
    def get_event_isolation(self, redis: Redis) -> BaseEventIsolation:
        return RedisEventIsolation(redis)


class UserGetterProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_user_getter(self, tg_client_config: TgClientConfig) -> AsyncIterable[UserGetter]:
        async with UserGetter(tg_client_config) as user_getter:
            yield user_getter


class BotIdpProvider(Provider):
    scope = Scope.REQUEST
    event = from_context(TelegramObject)
    aiogram_data = from_context(AiogramMiddlewareData)
    bot_idp = provide(TgBotIdentityProvider)


class BotOnlyIdpProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_idp(self, idp: TgBotIdentityProvider) -> IdentityProvider:
        return idp


class GameToolsProvider(Provider):
    @provide(scope=Scope.APP)
    def get_game_log(self, bot: Bot, config: BotConfig) -> GameLogWriter:
        return GameBotLog(bot=bot, log_chat_id=config.game_log_chat)

    @provide(scope=Scope.REQUEST)
    def get_hint_content_resolver(
        self, dao: HolderDao, file_storage: FileStorage
    ) -> HintContentResolver:
        return HintContentResolver(dao=dao.file_info, file_storage=file_storage)

    @provide(scope=Scope.APP)
    def get_org_notifier(self, bot: Bot) -> OrgNotifier:
        return BotOrgNotifier(bot=bot)

    get_hint_sender = provide(HintSender, scope=Scope.REQUEST)
    get_bot_game_view = provide(
        BotView, scope=Scope.REQUEST, provides=AnyOf[GameView, GameViewPreparer]
    )
    level_bot_view = provide(LevelBotView, scope=Scope.REQUEST, provides=LevelView)
    hint_parser = provide(HintParser, scope=Scope.REQUEST)
    results_painter = provide(ResultsPainter, scope=Scope.REQUEST)


def resolve_update_types(dp: Dispatcher) -> list[str]:
    return dp.resolve_used_update_types(skip_events={"aiogd_update"})
