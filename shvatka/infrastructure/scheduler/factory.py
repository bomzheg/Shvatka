from typing import AsyncIterable

from dishka import Provider, Scope, provide, AsyncContainer, AnyOf

from shvatka.core.interfaces.scheduler import Scheduler, LevelTestScheduler
from shvatka.infrastructure.db.config.models.db import RedisConfig
from shvatka.infrastructure.scheduler import ApScheduler


class SchedulerProvider(Provider):
    scope = Scope.APP

    @provide
    async def create_scheduler(
        self, dishka: AsyncContainer, redis_config: RedisConfig
    ) -> AsyncIterable[AnyOf[Scheduler, LevelTestScheduler]]:
        async with ApScheduler(dishka=dishka, redis_config=redis_config) as scheduler:
            yield scheduler
