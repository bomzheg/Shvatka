import asyncio
import secrets
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional, Set, Tuple

from aiogram import Bot, Dispatcher, loggers
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from aiogram.types import InputFile
from aiogram.webhook.security import IPFilter
from fastapi import FastAPI, Request, Response, HTTPException, APIRouter


def setup_application(app: FastAPI, dispatcher: Dispatcher, /, **kwargs: Any) -> None:
    """
    This function helps to configure a startup-shutdown process

    :param app: FastAPI application
    :param dispatcher: aiogram dispatcher
    :param kwargs: additional data
    :return:
    """
    workflow_data = {
        "app": app,
        "dispatcher": dispatcher,
        **dispatcher.workflow_data,
        **kwargs,
    }

    @asynccontextmanager
    async def lifespan(*a: Any, **kw: Any) -> None:  # pragma: no cover
        await dispatcher.emit_startup(**workflow_data)
        yield
        await dispatcher.emit_shutdown(**workflow_data)

    app.include_router(APIRouter(lifespan=lifespan))


def check_ip(ip_filter: IPFilter, request: Request) -> Tuple[str, bool]:
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
        dispatcher: Dispatcher,
        handle_in_background: bool = False,
        **data: Any,
    ) -> None:
        """
        Base handler that helps to handle incoming request from aiohttp
        and propagate it to the Dispatcher

        :param dispatcher: instance of :class:`aiogram.dispatcher.dispatcher.Dispatcher`
        :param handle_in_background: immediately responds to the Telegram instead of
            a waiting end of a handler process
        """
        self.dispatcher = dispatcher
        self.handle_in_background = handle_in_background
        self.data = data
        self._background_feed_update_tasks: Set[asyncio.Task[Any]] = set()

    def register(self, app: FastAPI, /, path: str, **kwargs: Any) -> None:

        router = APIRouter(prefix="/webhook", lifespan=self._handle_close)
        router.add_api_route(methods=["POST"], path=path, endpoint=self.handle, **kwargs)
        app.include_router(router)

    @asynccontextmanager
    async def _handle_close(self, app: FastAPI) -> None:
        yield
        await self.close()

    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    async def resolve_bot(self, request: Request) -> Bot:
        """
        This method should be implemented in subclasses of this class.

        Resolve Bot instance from request.

        :param request:
        :return: Bot instance
        """
        pass

    @abstractmethod
    def verify_secret(self, telegram_secret_token: str, bot: Bot) -> bool:
        pass

    async def _background_feed_update(self, bot: Bot, update: Dict[str, Any]) -> None:
        result = await self.dispatcher.feed_raw_update(bot=bot, update=update, **self.data)
        if isinstance(result, TelegramMethod):
            await self.dispatcher.silent_call_request(bot=bot, result=result)

    async def _handle_request_background(self, bot: Bot, request: Request) -> Response:
        feed_update_task = asyncio.create_task(
            self._background_feed_update(
                bot=bot, update=bot.session.json_loads(request.body)
            )
        )
        self._background_feed_update_tasks.add(feed_update_task)
        feed_update_task.add_done_callback(self._background_feed_update_tasks.discard)
        return Response(content={})

    def _build_response_writer(
        self, bot: Bot, result: Optional[TelegramMethod[TelegramType]]
    ) -> MultipartWriter:
        writer = MultipartWriter(
            "form-data",
            boundary=f"webhookBoundary{secrets.token_urlsafe(16)}",
        )
        if not result:
            return writer

        payload = writer.append(result.__api_method__)
        payload.set_content_disposition("form-data", name="method")

        files: Dict[str, InputFile] = {}
        for key, value in result.model_dump(warnings=False).items():
            value = bot.session.prepare_value(value, bot=bot, files=files)
            if not value:
                continue
            payload = writer.append(value)
            payload.set_content_disposition("form-data", name=key)

        for key, value in files.items():
            payload = writer.append(value.read(bot))
            payload.set_content_disposition(
                "form-data",
                name=key,
                filename=value.filename or key,
            )

        return writer

    async def _handle_request(self, bot: Bot, request: Request) -> Response:
        result: Optional[TelegramMethod[Any]] = await self.dispatcher.feed_webhook_update(
            bot,
            await request.json(loads=bot.session.json_loads),
            **self.data,
        )
        return Response(body=self._build_response_writer(bot=bot, result=result))

    async def handle(self, request: Request) -> Response:
        bot = await self.resolve_bot(request)
        if not self.verify_secret(request.headers.get("X-Telegram-Bot-Api-Secret-Token", ""), bot):
            return Response(content="Unauthorized", status_code=401)
        if self.handle_in_background:
            return await self._handle_request_background(bot=bot, request=request)
        return await self._handle_request(bot=bot, request=request)

    __call__ = handle


class SimpleRequestHandler(BaseRequestHandler):
    def __init__(
        self,
        dispatcher: Dispatcher,
        bot: Bot,
        handle_in_background: bool = True,
        secret_token: Optional[str] = None,
        **data: Any,
    ) -> None:
        """
        Handler for single Bot instance

        :param dispatcher: instance of :class:`aiogram.dispatcher.dispatcher.Dispatcher`
        :param handle_in_background: immediately responds to the Telegram instead of
            a waiting end of handler process
        :param bot: instance of :class:`aiogram.client.bot.Bot`
        """
        super().__init__(dispatcher=dispatcher, handle_in_background=handle_in_background, **data)
        self.bot = bot
        self.secret_token = secret_token

    def verify_secret(self, telegram_secret_token: str, bot: Bot) -> bool:
        if self.secret_token:
            return secrets.compare_digest(telegram_secret_token, self.secret_token)
        return True

    async def close(self) -> None:
        """
        Close bot session
        """
        await self.bot.session.close()

    async def resolve_bot(self, request: web.Request) -> Bot:
        return self.bot


class TokenBasedRequestHandler(BaseRequestHandler):
    def __init__(
        self,
        dispatcher: Dispatcher,
        handle_in_background: bool = True,
        bot_settings: Optional[Dict[str, Any]] = None,
        **data: Any,
    ) -> None:
        """
        Handler that supports multiple bots the context will be resolved
        from path variable 'bot_token'

        .. note::

            This handler is not recommended in due to token is available in URL
            and can be logged by reverse proxy server or other middleware.

        :param dispatcher: instance of :class:`aiogram.dispatcher.dispatcher.Dispatcher`
        :param handle_in_background: immediately responds to the Telegram instead of
            a waiting end of handler process
        :param bot_settings: kwargs that will be passed to new Bot instance
        """
        super().__init__(dispatcher=dispatcher, handle_in_background=handle_in_background, **data)
        if bot_settings is None:
            bot_settings = {}
        self.bot_settings = bot_settings
        self.bots: Dict[str, Bot] = {}

    def verify_secret(self, telegram_secret_token: str, bot: Bot) -> bool:
        return True

    async def close(self) -> None:
        for bot in self.bots.values():
            await bot.session.close()

    def register(self, app: Application, /, path: str, **kwargs: Any) -> None:
        """
        Validate path, register route and shutdown callback

        :param app: instance of aiohttp Application
        :param path: route path
        :param kwargs:
        """
        if "{bot_token}" not in path:
            raise ValueError("Path should contains '{bot_token}' substring")
        super().register(app, path=path, **kwargs)

    async def resolve_bot(self, request: web.Request) -> Bot:
        """
        Get bot token from a path and create or get from cache Bot instance

        :param request:
        :return:
        """
        token = request.match_info["bot_token"]
        if token not in self.bots:
            self.bots[token] = Bot(token=token, **self.bot_settings)
        return self.bots[token]
