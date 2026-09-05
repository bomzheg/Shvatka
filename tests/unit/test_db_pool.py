from prometheus_client.metrics import MetricWrapperBase
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool, QueuePool

from shvatka.infrastructure.db.factory import create_engine, pool_options
from shvatka.infrastructure.db.metrics import (
    DB_POOL_CHECKED_OUT,
    DB_POOL_CHECKOUT_SECONDS,
    DB_POOL_SIZE,
    instrument_pool,
)
from tests.mocks.config import DBConfig

URI = "postgresql+asyncpg://u:p@localhost:5432/db"


def test_postgres_pool_is_sized_from_config():
    config = DBConfig(URI)
    config.pool_size = 20
    config.max_overflow = 7

    options = pool_options(config, make_url(config.uri))

    assert options["pool_size"] == 20
    assert options["max_overflow"] == 7
    assert options["pool_timeout"] == 30.0


def test_sqlite_gets_no_pool_sizing():
    config = DBConfig("sqlite+aiosqlite:///:memory:")

    assert {} == pool_options(config, make_url(config.uri))


def test_engine_carries_the_configured_pool():
    config = DBConfig(URI)
    config.pool_size = 11
    config.max_overflow = 3

    engine = create_engine(config)

    assert isinstance(engine.pool, QueuePool)
    assert engine.pool.size() == 11
    assert engine.pool._max_overflow == 3


def test_a_checkout_is_measured_and_the_gauges_follow():
    config = DBConfig(URI)
    config.pool_size = 9
    engine = create_engine(config)
    before = checkout_count()

    record = FakeRecord()
    checkout(engine, record)
    checkin(engine, record)

    assert checkout_count() == before + 1
    assert sample(DB_POOL_SIZE) == 9
    assert sample(DB_POOL_CHECKED_OUT) == 0, "nothing was really checked out"


def test_a_checkin_without_a_checkout_measures_nothing():
    engine = create_engine(DBConfig(URI))
    before = checkout_count()

    checkin(engine, FakeRecord())

    assert checkout_count() == before


def test_a_pool_that_does_not_queue_is_left_alone():
    engine = create_async_engine(URI, poolclass=NullPool)

    instrument_pool(engine)

    assert not engine.sync_engine.pool.dispatch.checkout


class FakeRecord:
    def __init__(self) -> None:
        self.info: dict[str, object] = {}


def checkout(engine: AsyncEngine, record: FakeRecord) -> None:
    engine.sync_engine.pool.dispatch.checkout(None, record, None)


def checkin(engine: AsyncEngine, record: FakeRecord) -> None:
    engine.sync_engine.pool.dispatch.checkin(None, record)


def checkout_count() -> float:
    return sample(DB_POOL_CHECKOUT_SECONDS, suffix="_count")


def sample(metric: MetricWrapperBase, suffix: str = "") -> float:
    samples = [one for family in metric.collect() for one in family.samples]
    if not suffix:
        return samples[0].value
    return next(one.value for one in samples if one.name.endswith(suffix))
