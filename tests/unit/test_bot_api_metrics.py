from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import GetMe, SendMessage
from prometheus_client import REGISTRY

from shvatka.tgbot.utils.metrics import RequestMetricsMiddleware


def get_value(name: str, labels: dict[str, str]) -> float:
    return REGISTRY.get_sample_value(name, labels) or 0.0


@pytest.mark.asyncio
async def test_success_request_counted():
    method = GetMe()
    labels = {"method": "GetMe"}
    requests_before = get_value("tgbot_api_requests_total", labels)
    responses_before = get_value("tgbot_api_responses_total", {**labels, "status": "success"})
    duration_before = get_value("tgbot_api_request_duration_seconds_count", labels)

    async def make_request(bot, method_):
        return "result"

    result = await RequestMetricsMiddleware()(make_request, AsyncMock(), method)

    assert result == "result"
    assert get_value("tgbot_api_requests_total", labels) == requests_before + 1
    assert (
        get_value("tgbot_api_responses_total", {**labels, "status": "success"})
        == responses_before + 1
    )
    assert get_value("tgbot_api_request_duration_seconds_count", labels) == duration_before + 1
    assert get_value("tgbot_api_requests_in_progress", labels) == 0


@pytest.mark.asyncio
async def test_failed_request_counted():
    method = SendMessage(chat_id=1, text="hello")
    labels = {"method": "SendMessage"}
    requests_before = get_value("tgbot_api_requests_total", labels)
    errors_before = get_value(
        "tgbot_api_responses_total", {**labels, "status": "TelegramBadRequest"}
    )

    async def make_request(bot, method_):
        raise TelegramBadRequest(method=method_, message="chat not found")

    with pytest.raises(TelegramBadRequest):
        await RequestMetricsMiddleware()(make_request, AsyncMock(), method)

    assert get_value("tgbot_api_requests_total", labels) == requests_before + 1
    assert (
        get_value("tgbot_api_responses_total", {**labels, "status": "TelegramBadRequest"})
        == errors_before + 1
    )
    assert get_value("tgbot_api_requests_in_progress", labels) == 0
