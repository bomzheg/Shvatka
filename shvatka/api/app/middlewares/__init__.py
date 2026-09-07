from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from shvatka.api.app.config.models.main import ApiConfig
from shvatka.api.app.middlewares.log import LoggingMiddleware


def setup(app: FastAPI, config: ApiConfig) -> None:
    if config.api.enable_logging:
        app.add_middleware(LoggingMiddleware)
    if config.api.auth.disable_cors:
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
