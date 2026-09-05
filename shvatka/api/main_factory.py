import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from asgi_monitor.integrations.fastapi import MetricsConfig, setup_metrics
from fastapi import FastAPI
from prometheus_client import REGISTRY

from shvatka.api.app import error_handler, middlewares, router
from shvatka.api.app.config.models.main import ApiConfig
from shvatka.common.config.models.main import Config
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.common.docs import DocsUrlFactory
from shvatka.common.loop_monitor import LoopMonitor

logger = logging.getLogger(__name__)


def create_app(config: ApiConfig) -> FastAPI:
    app = FastAPI()
    app.include_router(router.setup())
    middlewares.setup(app, config)
    error_handler.setup(app, DocsUrlFactory(config.docs))
    setup_metrics(
        app,
        MetricsConfig(
            app_name=config.app.name,
            include_metrics_endpoint=True,
            include_trace_exemplar=True,
            # the global registry, so that metrics collected outside of asgi
            # (e.g. outgoing bot api requests) are exposed by /metrics too
            registry=REGISTRY,
        ),
    )

    return app


def setup_loop_monitor(root_app: FastAPI, config: Config) -> None:
    monitor = LoopMonitor(config.monitoring)

    async def start() -> None:
        set_blocking_threads(config.monitoring.blocking_threads)
        await monitor.start()

    root_app.router.add_event_handler("startup", start)
    root_app.router.add_event_handler("shutdown", monitor.stop)


def set_blocking_threads(size: int | None) -> None:
    if size is None:
        return
    executor = ThreadPoolExecutor(max_workers=size, thread_name_prefix="shvatka-blocking")
    asyncio.get_running_loop().set_default_executor(executor)
    logger.info("blocking work runs in a pool of %s threads", size)


def get_paths() -> Paths:
    return common_get_paths("API_PATH")
