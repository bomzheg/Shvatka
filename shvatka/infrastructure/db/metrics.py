import logging
import time

from prometheus_client import Gauge, Histogram
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

_CHECKED_OUT_AT = "shvatka_checked_out_at"

DB_POOL_CHECKED_OUT = Gauge(
    "db_pool_checked_out",
    "connections currently held by a caller",
)
DB_POOL_SIZE = Gauge(
    "db_pool_size",
    "connections the pool keeps open",
)
DB_POOL_OVERFLOW = Gauge(
    "db_pool_overflow",
    "connections opened past pool_size; equals max_overflow when the pool is exhausted",
)
DB_POOL_CHECKOUT_SECONDS = Histogram(
    "db_pool_checkout_seconds",
    "how long one connection stayed checked out",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)


def instrument_pool(engine: AsyncEngine) -> None:
    pool = engine.pool
    if not isinstance(pool, QueuePool):
        logger.info("pool %s does not queue, not reporting it", type(pool).__name__)
        return

    @event.listens_for(engine.sync_engine, "checkout")
    def _on_checkout(dbapi_connection, connection_record, connection_proxy) -> None:
        connection_record.info[_CHECKED_OUT_AT] = time.monotonic()
        _observe_pool(engine)

    @event.listens_for(engine.sync_engine, "checkin")
    def _on_checkin(dbapi_connection, connection_record) -> None:
        started = connection_record.info.pop(_CHECKED_OUT_AT, None)
        if started is not None:
            DB_POOL_CHECKOUT_SECONDS.observe(time.monotonic() - started)
        _observe_pool(engine)


def _observe_pool(engine: AsyncEngine) -> None:
    pool = engine.pool
    DB_POOL_CHECKED_OUT.set(pool.checkedout())  # type: ignore[attr-defined]
    DB_POOL_SIZE.set(pool.size())  # type: ignore[attr-defined]
    DB_POOL_OVERFLOW.set(pool.overflow())  # type: ignore[attr-defined]
