import logging

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not logger.isEnabledFor(logging.DEBUG):
            await self.app(scope, receive, send)
            return
        logger.debug(
            "got request. method: %s, path: %s, headers: %s",
            scope.get("method"),
            scope.get("path"),
            scope.get("headers"),
        )

        async def send_logged(message: Message) -> None:
            if message["type"] == "http.response.start":
                logger.debug(
                    "response will be: status: %s, headers: %s",
                    message["status"],
                    message.get("headers"),
                )
            await send(message)

        await self.app(scope, receive, send_logged)
