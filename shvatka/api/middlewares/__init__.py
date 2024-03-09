from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from shvatka.api.config.models.main import ApiConfig
from shvatka.api.middlewares.log import LoggingMiddleware


def setup(app: FastAPI, config: ApiConfig) -> None:
    if config.enable_logging:
        app.add_middleware(BaseHTTPMiddleware, dispatch=LoggingMiddleware())
    if config.auth.disable_cors:
        patch_for_cors(app)


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
