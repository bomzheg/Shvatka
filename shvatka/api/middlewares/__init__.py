from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from shvatka.api.middlewares.log import LoggingMiddleware


def setup(app: FastAPI) -> None:
    app.add_middleware(BaseHTTPMiddleware, dispatch=LoggingMiddleware())
