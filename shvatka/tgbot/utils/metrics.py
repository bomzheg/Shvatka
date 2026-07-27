import time

from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.methods import Response, TelegramMethod
from aiogram.methods.base import TelegramType
from prometheus_client import REGISTRY, Counter, Gauge, Histogram

PREFIX = "tgbot_api"
SUCCESS_STATUS = "success"

requests_total = Counter(
    name=f"{PREFIX}_requests_total",
    documentation="Total count of requests sent to Telegram Bot API by method",
    labelnames=["method"],
    registry=REGISTRY,
)
responses_total = Counter(
    name=f"{PREFIX}_responses_total",
    documentation=(
        "Total count of Telegram Bot API responses by method and status "
        "(success or the name of the raised error)"
    ),
    labelnames=["method", "status"],
    registry=REGISTRY,
)
request_duration = Histogram(
    name=f"{PREFIX}_request_duration_seconds",
    documentation="Histogram of Telegram Bot API request duration by method, in seconds",
    labelnames=["method"],
    registry=REGISTRY,
)
requests_in_progress = Gauge(
    name=f"{PREFIX}_requests_in_progress",
    documentation="Gauge of Telegram Bot API requests by method currently in progress",
    labelnames=["method"],
    registry=REGISTRY,
)


class RequestMetricsMiddleware(BaseRequestMiddleware):
    """Collects prometheus metrics of outgoing Telegram Bot API requests."""

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        method_name = type(method).__name__
        status = SUCCESS_STATUS
        requests_total.labels(method=method_name).inc()
        requests_in_progress.labels(method=method_name).inc()
        started_at = time.perf_counter()
        try:
            return await make_request(bot, method)
        except Exception as e:
            status = type(e).__name__
            raise
        finally:
            request_duration.labels(method=method_name).observe(time.perf_counter() - started_at)
            responses_total.labels(method=method_name, status=status).inc()
            requests_in_progress.labels(method=method_name).dec()


def setup_metrics(bot: Bot) -> None:
    bot.session.middleware(RequestMetricsMiddleware())
