import logging

from asgi_monitor.integrations.fastapi import setup_metrics  # type: ignore[import-untyped]
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from shvatka.api import routes, middlewares
from shvatka.api.config.models.main import ApiConfig
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.paths import common_get_paths

logger = logging.getLogger(__name__)


def create_app(config: ApiConfig) -> FastAPI:
    app = FastAPI()
    app.include_router(routes.setup())
    middlewares.setup(app)
    setup_metrics(
        app, app_name=config.app.name, include_metrics_endpoint=True, include_trace_exemplar=True
    )
    if config.auth.disable_cors:
        patch_for_cors(app)
    return app


def patch_for_cors(app: FastAPI):
    origins = [
        "http://localhost:4200",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def get_paths() -> Paths:
    return common_get_paths("API_PATH")
