import logging

from asgi_monitor.integrations.fastapi import setup_metrics  # type: ignore[import-untyped]
from fastapi import FastAPI

from shvatka.api import routes, middlewares
from shvatka.api.config.models.main import ApiConfig
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.paths import common_get_paths

logger = logging.getLogger(__name__)


def create_app(config: ApiConfig) -> FastAPI:
    app = FastAPI()
    app.include_router(routes.setup())
    middlewares.setup(app, config)
    setup_metrics(
        app, app_name=config.app.name, include_metrics_endpoint=True, include_trace_exemplar=True
    )

    return app


def get_paths() -> Paths:
    return common_get_paths("API_PATH")
