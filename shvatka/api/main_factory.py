import logging

from fastapi import FastAPI

from shvatka.api import routes, middlewares
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.paths import common_get_paths

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(routes.setup())
    middlewares.setup(app)
    return app


def get_paths() -> Paths:
    return common_get_paths("API_PATH")
