import asyncio
import threading
from dataclasses import replace

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI

from shvatka.api.main_factory import setup_blocking_pool, setup_loop_monitor
from shvatka.common.config.models.main import Config
from shvatka.common.config.models.monitoring import MonitoringConfig


def app_with(config: Config) -> FastAPI:
    root_app = FastAPI()
    root_app.mount("/context/path", FastAPI())
    setup_blocking_pool(root_app, config)
    setup_loop_monitor(root_app, config)
    return root_app


@pytest.mark.asyncio
async def test_the_pool_is_sized_even_with_monitoring_off(bot_config: Config):
    # sizing the pool is about how work runs, not about watching it, so one
    # must not switch off the other
    config = replace(
        bot_config,
        app=replace(bot_config.app, blocking_threads=2),
        monitoring=MonitoringConfig(enabled=False),
    )

    async with LifespanManager(app_with(config)):
        worker = await asyncio.to_thread(threading.current_thread)

    assert worker.name.startswith("shvatka-blocking")


@pytest.mark.asyncio
async def test_python_sizes_it_when_the_config_says_nothing(bot_config: Config):
    config = replace(bot_config, app=replace(bot_config.app, blocking_threads=None))

    async with LifespanManager(app_with(config)):
        worker = await asyncio.to_thread(threading.current_thread)

    assert not worker.name.startswith("shvatka-blocking")
