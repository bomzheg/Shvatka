import logging
import os
from typing import Iterable

from dishka import provide, Scope, Provider
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from shvatka.common import Config
from shvatka.infrastructure.db.config.models.db import RedisConfig
from shvatka.infrastructure.db.config.models.db import DBConfig as TrueConfig
from tests.mocks.config import DBConfig

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
