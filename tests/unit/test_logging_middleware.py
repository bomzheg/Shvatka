import logging

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from shvatka.api.app.middlewares.log import LoggingMiddleware
from tests.utils.logs import capture_logs

LOGGER = "shvatka.api.app.middlewares.log"


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)
    app.get("/ping")(lambda: {"ok": True})
    return app


async def get(app: FastAPI, path: str = "/ping"):
    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        return await client.get(path)


@pytest.mark.asyncio
async def test_it_passes_the_request_through(app: FastAPI):
    response = await get(app)

    assert response.status_code == 200
    assert {"ok": True} == response.json()


@pytest.mark.asyncio
async def test_it_logs_the_request_and_the_status(app: FastAPI):
    with capture_logs(LOGGER) as logs:
        await get(app)

    assert "path: /ping" in logs.text
    assert "status: 200" in logs.text


@pytest.mark.asyncio
async def test_it_says_nothing_when_debug_is_off(app: FastAPI):
    with capture_logs(LOGGER, logging.INFO) as logs:
        await get(app)

    assert [] == logs.records
