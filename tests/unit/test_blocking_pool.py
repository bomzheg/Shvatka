import asyncio
import threading
from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import TypeVar

from asgi_lifespan import LifespanManager
from fastapi import FastAPI

from shvatka.api.main_factory import setup_blocking_pool, setup_loop_monitor
from shvatka.common.config.models.main import Config
from shvatka.common.config.models.monitoring import MonitoringConfig

T = TypeVar("T")


# `set_default_executor` is loop-global and sticky, and the suite's event_loop
# fixture is session-scoped — sizing the pool inside it would hand every later
# test a two-thread executor. Each case gets a loop of its own instead.
def in_a_fresh_loop(main: Callable[[], Awaitable[T]]) -> T:
    return asyncio.run(main())


def worker_thread_name(config: Config) -> str:
    async def main() -> str:
        root_app = FastAPI()
        root_app.mount("/context/path", FastAPI())
        setup_blocking_pool(root_app, config)
        setup_loop_monitor(root_app, config)
        async with LifespanManager(root_app):
            worker = await asyncio.to_thread(threading.current_thread)
        return worker.name

    return in_a_fresh_loop(main)


def test_the_pool_is_sized_even_with_monitoring_off(bot_config: Config):
    # sizing the pool is about how work runs, not about watching it, so one
    # must not switch off the other
    config = replace(
        bot_config,
        app=replace(bot_config.app, blocking_threads=2),
        monitoring=MonitoringConfig(enabled=False),
    )

    assert worker_thread_name(config).startswith("shvatka-blocking")


def test_python_sizes_it_when_the_config_says_nothing(bot_config: Config):
    config = replace(bot_config, app=replace(bot_config.app, blocking_threads=None))

    assert not worker_thread_name(config).startswith("shvatka-blocking")
