from typing import AsyncIterable

from aiogram import Bot
from dishka import Provider, Scope, provide, AsyncContainer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.infrastructure.db.config.models.db import RedisConfig
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.scheduler import ApScheduler
from shvatka.tgbot.config.models.bot import BotConfig


class SchedulerProvider(Provider):
    scope = Scope.APP

    @provide
    async def create_scheduler(
        self,
        pool: async_sessionmaker[AsyncSession],
        redis: Redis,
        bot: Bot,
        redis_config: RedisConfig,
        config: BotConfig,
        file_storage: FileStorage,
        level_test_dao: LevelTestingData,
        dishka: AsyncContainer,
    ) -> AsyncIterable[Scheduler]:
        async with ApScheduler(
            redis_config=redis_config,
            pool=pool,
            redis=redis,
            bot=bot,
            game_log_chat=config.game_log_chat,
            file_storage=file_storage,
            level_test_dao=level_test_dao,
        ) as scheduler:
            yield scheduler
