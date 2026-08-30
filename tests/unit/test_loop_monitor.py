"""The monitor that says when the event loop stopped serving, and why.

Everything here is about a loop that is deliberately blocked, so the tests
block it with ``time.sleep`` — which is exactly the mistake the monitor exists
to catch in production code.
"""

import asyncio
import logging
import time

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from prometheus_client.metrics import MetricWrapperBase

from shvatka.api.main_factory import setup_loop_monitor
from shvatka.common.config.models.main import Config
from shvatka.common.config.models.monitoring import MonitoringConfig
from shvatka.common.loop_monitor import LOOP_LAG, LOOP_STALLS, LoopMonitor


def lag_count() -> float:
    return _sample(LOOP_LAG, "_count")


def stall_count() -> float:
    return _sample(LOOP_STALLS, "_total")


def _sample(metric: MetricWrapperBase, suffix: str) -> float:
    return next(
        sample.value
        for family in metric.collect()
        for sample in family.samples
        if sample.name.endswith(suffix)
    )


@pytest.fixture
def config() -> MonitoringConfig:
    return MonitoringConfig(
        probe_interval=0.01,
        stall_threshold=0.1,
        stall_report_interval=0.0,
    )


@pytest.mark.asyncio
async def test_measures_a_loop_that_is_not_blocked(config: MonitoringConfig):
    before = lag_count()
    monitor = LoopMonitor(config)
    await monitor.start()
    try:
        await asyncio.sleep(config.probe_interval * 5)
    finally:
        await monitor.stop()

    assert lag_count() > before, "the probe recorded nothing"


@pytest.mark.asyncio
async def test_reports_the_stack_that_blocked_the_loop(
    config: MonitoringConfig, caplog: pytest.LogCaptureFixture
):
    before = stall_count()
    monitor = LoopMonitor(config)
    await monitor.start()
    try:
        with caplog.at_level(logging.WARNING, logger="shvatka.common.loop_monitor"):
            await asyncio.sleep(config.probe_interval)
            block_the_loop(config.stall_threshold * 4)
            # the watchdog needs a turn of its own to notice, and the probe
            # needs one to mark the loop as running again
            await asyncio.sleep(config.probe_interval * 10)
    finally:
        await monitor.stop()

    assert stall_count() > before, "the stall went uncounted"
    assert "event loop blocked for" in caplog.text
    assert "block_the_loop" in caplog.text, "the traceback does not name the culprit"


@pytest.mark.asyncio
async def test_stop_is_idempotent(config: MonitoringConfig):
    monitor = LoopMonitor(config)
    await monitor.start()
    await monitor.stop()
    await monitor.stop()


@pytest.mark.asyncio
async def test_watchdog_can_be_switched_off(config: MonitoringConfig):
    monitor = LoopMonitor(
        MonitoringConfig(
            probe_interval=config.probe_interval,
            stall_threshold=config.stall_threshold,
            stall_traceback=False,
        )
    )
    await monitor.start()
    try:
        assert monitor._watchdog is None
    finally:
        await monitor.stop()


def block_the_loop(seconds: float) -> None:
    """Named so that the reported traceback is recognisable."""
    time.sleep(seconds)


@pytest.mark.asyncio
async def test_it_runs_when_the_app_is_mounted_under_a_root(bot_config: Config):
    """Starlette does not run the lifespan of a mounted sub-application, so the
    monitor is registered on the root app. Moving it onto the one ``create_app``
    builds would silently stop it from ever starting.
    """
    root_app = FastAPI()
    root_app.mount("/context/path", FastAPI())
    setup_loop_monitor(root_app, bot_config)
    before = lag_count()

    async with LifespanManager(root_app):
        await asyncio.sleep(bot_config.monitoring.probe_interval * 3)

    assert lag_count() > before, "the monitor never started"
