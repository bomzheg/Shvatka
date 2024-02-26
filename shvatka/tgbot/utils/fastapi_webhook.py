import asyncio
import secrets
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Annotated

from aiogram import Bot, Dispatcher, loggers
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from aiogram.webhook.security import IPFilter
from dishka import AsyncContainer
from dishka.integrations.base import Depends
from dishka.integrations.fastapi import inject
from fastapi import FastAPI, Request, Response, HTTPException, APIRouter


def setup_application(app: FastAPI, dishka: AsyncContainer, /, **kwargs: Any) -> None:
    workflow_data = {
        "app": app,
        "dishka": dishka,
        **kwargs,
    }

    @asynccontextmanager
    async def lifespan(*a: Any, **kw: Any):
        dispatcher = await dishka.get(Dispatcher)
        await dispatcher.emit_startup(**workflow_data, **dispatcher.workflow_data)
        yield
        await dispatcher.emit_shutdown(**workflow_data, **dispatcher.workflow_data)

    app.include_router(APIRouter(lifespan=lifespan))


def check_ip(ip_filter: IPFilter, request: Request) -> tuple[str, bool]:
    # Try to resolve client IP over reverse proxy
    if forwarded_for := request.headers.get("X-Forwarded-For", ""):
        forwarded_for, *_ = forwarded_for.split(",", maxsplit=1)
        return forwarded_for, forwarded_for in ip_filter

    # no implementation without reverse proxy
    return "", False


class IpFilterMiddleware:
    def __init__(self, ip_filter: IPFilter) -> None:
        self.ip_filter = ip_filter

    async def __call__(self, request: Request, call_next) -> Response:
        ip_address, accept = check_ip(ip_filter=self.ip_filter, request=request)
        if not accept:
            loggers.webhook.warning("Blocking request from an unauthorized IP: %s", ip_address)
            raise HTTPException(status_code=401, detail="Blocking request from an unauthorized")
        return await call_next(request)


class BaseRequestHandler(ABC):
    def __init__(
        self,
        handle_in_background: bool = False,
        **data: Any,
    ) -> None:
        self.handle_in_background = handle_in_background
        self.data = data
        self._background_feed_update_tasks: set[asyncio.Task[Any]] = set()

    def register(self, app: FastAPI, /, path: str, **kwargs: Any) -> None:
        router = APIRouter(prefix="/webhook")
        router.add_api_route(methods=["POST"], path=path, endpoint=self.handle, **kwargs)
        app.include_router(router)

    @abstractmethod
    def verify_secret(self, telegram_secret_token: str, bot: Bot) -> bool:
        pass

    async def _background_feed_update(
        self, bot: Bot, dispatcher: Dispatcher, update: dict[str, Any]
    ) -> None:
        result = await dispatcher.feed_raw_update(bot=bot, update=update, **self.data)
        if isinstance(result, TelegramMethod):
            await dispatcher.silent_call_request(bot=bot, result=result)

    async def _handle_request_background(
        self, bot: Bot, dispatcher: Dispatcher, request: Request
    ) -> Response:
        feed_update_task = asyncio.create_task(
            self._background_feed_update(
                bot=bot, dispatcher=dispatcher, update=bot.session.json_loads(request.body)
            )
        )
        self._background_feed_update_tasks.add(feed_update_task)
        feed_update_task.add_done_callback(self._background_feed_update_tasks.discard)
        return Response(content={})

    async def _build_response_writer(
        self, bot: Bot, dispatcher: Dispatcher, result: TelegramMethod[TelegramType] | None
    ) -> Any:
        if result:
            # TODO response to webhook
            await dispatcher.silent_call_request(bot, result)

    async def _handle_request(
        self, bot: Bot, dispatcher: Dispatcher, request: Request
    ) -> Response:
        result: TelegramMethod[Any] | None = await dispatcher.feed_webhook_update(
            bot,
            await request.json(),
            **self.data,
        )
        return Response(
            content=await self._build_response_writer(
                bot=bot, dispatcher=dispatcher, result=result
            )
        )

    @inject
    async def handle(
        self,
        request: Request,
        bot: Annotated[Bot, Depends()],
        dispatcher: Annotated[Dispatcher, Depends()],
    ) -> Response:
        if not self.verify_secret(request.headers.get("X-Telegram-Bot-Api-Secret-Token", ""), bot):
            return Response(content="Unauthorized", status_code=401)
        if self.handle_in_background:
            return await self._handle_request_background(
                bot=bot, dispatcher=dispatcher, request=request
            )
        return await self._handle_request(bot=bot, dispatcher=dispatcher, request=request)

    __call__ = handle


class SimpleRequestHandler(BaseRequestHandler):
    def __init__(
        self,
        handle_in_background: bool = True,
        secret_token: str | None = None,
        **data: Any,
    ) -> None:
        """
        Handler for single Bot instance

        :param dispatcher: instance of :class:`aiogram.dispatcher.dispatcher.Dispatcher`
        :param handle_in_background: immediately responds to the Telegram instead of
            a waiting end of handler process
        :param bot: instance of :class:`aiogram.client.bot.Bot`
        """
        super().__init__(handle_in_background=handle_in_background, **data)
        self.secret_token = secret_token

    def verify_secret(self, telegram_secret_token: str, bot: Bot) -> bool:
        if self.secret_token:
            return secrets.compare_digest(telegram_secret_token, self.secret_token)
        return True
