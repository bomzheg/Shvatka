import logging

from asgi_monitor.integrations.fastapi import MetricsConfig, setup_metrics
from fastapi import FastAPI
from prometheus_client import REGISTRY

from shvatka.api.app import error_handler, middlewares, router
from shvatka.api.app.config.models.main import ApiConfig
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.common.docs import DocsUrlFactory

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


def get_paths() -> Paths:
    return common_get_paths("API_PATH")
