import logging
import os

import pytest
import pytest_asyncio
from aiogram import Dispatcher, Bot
from dataclass_factory import Factory
from mockito import mock
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, close_all_sessions
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from shvatka.dao.holder import HolderDao
from shvatka.dao.redis.base import create_redis
from shvatka.models.config import Config
from shvatka.services.scheduler import Scheduler
from shvatka.services.username_resolver.user_getter import UserGetter
from tests.fixtures.conftest import fixtures_resource_path  # noqa: F401
from tests.fixtures.scn_fixtures import simple_scn  # noqa: F401
from tests.mocks.config import DBConfig
from tgbot.main_factory import create_dispatcher, create_scheduler

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def dao(session: AsyncSession, redis: Redis) -> HolderDao:
    dao_ = HolderDao(session=session, redis=redis)
    await clear_data(dao_)
    return dao_


async def clear_data(dao: HolderDao):
    await dao.poll.delete_all()
    await dao.waiver.delete_all()
    await dao.level.delete_all()
    await dao.game.delete_all()
    await dao.player_in_team.delete_all()
    await dao.team.delete_all()
    await dao.chat.delete_all()
    await dao.player.delete_all()
    await dao.user.delete_all()
    await dao.commit()


@pytest_asyncio.fixture
async def session(pool: sessionmaker) -> AsyncSession:
    async with pool() as session_:
        yield session_


@pytest.fixture(scope="session")
def pool(postgres_url: str) -> sessionmaker:
    engine = create_async_engine(url=postgres_url)
    pool_ = sessionmaker(bind=engine, class_=AsyncSession,
                         expire_on_commit=False, autoflush=False)
    yield pool_
    close_all_sessions()


@pytest.fixture(scope="session")
def postgres_url(app_config: Config) -> str:
    if os.name == "nt":  # windows testcontainers now not working
        yield app_config.db.uri
    else:
        with PostgresContainer("postgres:11") as postgres:
            postgres_url_ = postgres.get_connection_url().replace("psycopg2", "asyncpg")
            logger.info("postgres url %s", postgres_url_)
            app_config.db = DBConfig(postgres_url_)
            yield postgres_url_


@pytest_asyncio.fixture(scope="session")
async def redis(app_config: Config) -> Redis:
    if os.name == "nt":  # windows testcontainers now not working
        async with create_redis(app_config.redis) as r:
            yield r
    else:
        with RedisContainer("redis:latest") as redis_container:
            url = redis_container.get_container_host_ip()
            port = redis_container.get_exposed_port(redis_container.port_to_expose)
            app_config.redis.url = url
            app_config.redis.port = port
            r = create_redis(app_config.redis)
            yield r


@pytest_asyncio.fixture(scope="session")
async def scheduler(pool: sessionmaker, redis: Redis, bot: Bot, app_config: Config):
    s = create_scheduler(pool=pool, redis=redis, bot=bot, redis_config=app_config.redis)
    await s.start()
    yield s
    await s.close()


@pytest.fixture(scope="session")
def dp(
    pool: sessionmaker, app_config: Config, user_getter: UserGetter,
    dcf: Factory, redis: Redis, scheduler: Scheduler,
) -> Dispatcher:
    return create_dispatcher(
        config=app_config, user_getter=user_getter, dcf=dcf, pool=pool,
        redis=redis, scheduler=scheduler,
    )


@pytest.fixture(scope="session")
def user_getter() -> UserGetter:
    dummy = mock(UserGetter)
    return dummy


@pytest.fixture(scope="session")
def bot(app_config: Config) -> Bot:
    dummy = mock(Bot)
    setattr(dummy, "id", 123)
    return dummy
