import logging
from typing import AsyncIterable

from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseStorage, BaseEventIsolation
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder, RedisEventIsolation
from aiogram_dialog.manager.message_manager import MessageManager
from dataclass_factory import Factory
from dishka import AsyncContainer, make_async_container, Provider, Scope, provide
from redis.asyncio import Redis

from shvatka.common.factory import TelegraphProvider, DCFProvider
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.db.config.models.storage import StorageConfig, StorageType
from shvatka.infrastructure.db.factory import (
    create_redis,
    create_lock_factory,
)
from shvatka.infrastructure.di import get_providers
from shvatka.infrastructure.scheduler.factory import SchedulerProvider
from shvatka.tgbot.config.models.bot import BotConfig, TgClientConfig
from shvatka.tgbot.handlers import setup_handlers
from shvatka.tgbot.middlewares import setup_middlewares
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.utils.router import print_router_tree

logger = logging.getLogger(__name__)


def create_dishka(paths_env: str) -> AsyncContainer:
    container = make_async_container(*get_bot_providers(paths_env))
    return container


def get_bot_providers(paths_env: str) -> list[Provider]:
    return [
        *get_providers(paths_env),
        DpProvider(),
        DialogManagerProvider(),
        SchedulerProvider(),
        TelegraphProvider(),
        DCFProvider(),
    ]


class DialogManagerProvider(Provider):
    scope = Scope.APP

    @provide
    def get_manager(self) -> MessageManager:
        return MessageManager()


class DpProvider(Provider):
    scope = Scope.APP

    @provide
    def get_lock_factory(self) -> KeyCheckerFactory:
        return create_lock_factory()

    @provide
    async def get_user_getter(self, tg_client_config: TgClientConfig) -> AsyncIterable[UserGetter]:
        async with UserGetter(tg_client_config) as user_getter:
            yield user_getter

    @provide
    def create_dispatcher(
        self,
        dishka: AsyncContainer,
        event_isolation: BaseEventIsolation,
        bot_config: BotConfig,
        storage: BaseStorage,
        message_manager: MessageManager,
    ) -> Dispatcher:
        dp = Dispatcher(
            storage=storage,
            events_isolation=event_isolation,
        )
        bg_manager_factory = setup_handlers(dp, bot_config, message_manager)
        setup_middlewares(
            dishka=dishka,
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


def resolve_update_types(dp: Dispatcher) -> list[str]:
    return dp.resolve_used_update_types(skip_events={"aiogd_update"})
