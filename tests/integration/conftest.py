import logging

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer


logger = logging.getLogger(__name__)


@pytest.fixture
async def session(pool: sessionmaker) -> AsyncSession:
    async with pool() as session:
        yield session


@pytest.fixture(scope="session")
def pool(postgres_url: str) -> sessionmaker:
    engine = create_async_engine(url=postgres_url)
    pool_ = sessionmaker(bind=engine, class_=AsyncSession,
                         expire_on_commit=False, autoflush=False)
    return pool_


@pytest.fixture(scope="session")
def postgres_url() -> str:
    with PostgresContainer("postgres:11") as postgres:
        postgres_url = postgres.get_connection_url().replace("psycopg2", "asyncpg")
        logger.info("postgres url %s", postgres_url)
        yield postgres_url

