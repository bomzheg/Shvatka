import logging
import os
from typing import Iterable

from dishka import provide, Scope, Provider
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from shvatka.common import Config
from shvatka.infrastructure.db.config.models.db import RedisConfig
from shvatka.infrastructure.db.config.models.db import DBConfig as TrueConfig
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from tests.mocks.config import DBConfig
from tests.mocks.datetime_mock import ClockMock

logger = logging.getLogger(__name__)


class TestDbProvider(Provider):
    scope = Scope.APP

    @provide
    def get_db_config(self, config: Config) -> Iterable[TrueConfig]:
        postgres = PostgresContainer("postgres:16.1")
        if os.name == "nt":  # TODO workaround from testcontainers/testcontainers-python#108
            postgres.get_container_host_ip = lambda: "localhost"
        try:
            postgres.start()
            postgres_url_ = postgres.get_connection_url().replace("psycopg2", "asyncpg")
            logger.info("postgres url %s", postgres_url_)
            db_config = DBConfig(postgres_url_)
            db_config.echo = config.db.echo
            config.db = db_config
            yield db_config
        finally:
            postgres.stop()

    @provide
    def get_redis_config(self, config: Config) -> Iterable[RedisConfig]:
        redis_container = RedisContainer("redis:6.2.13-alpine")
        if os.name == "nt":  # TODO workaround from testcontainers/testcontainers-python#108
            redis_container.get_container_host_ip = lambda: "localhost"
        try:
            redis_container.start()
            url = redis_container.get_container_host_ip()
            port = redis_container.get_exposed_port(redis_container.port)
            r = RedisConfig(url=url, port=int(port))
            yield r
        finally:
            redis_container.stop()

    @provide(scope=Scope.REQUEST)
    async def get_dao(
        self,
        session: AsyncSession,
        redis: Redis,
        level_test: LevelTestingData,
        clock: ClockMock,
    ) -> HolderDao:
        return HolderDao(session=session, redis=redis, level_test=level_test, clock=clock)
