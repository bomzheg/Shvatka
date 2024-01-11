import logging

from fastapi import Request, Response

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    async def __call__(self, request: Request, call_next) -> Response:
        logger.debug("got request. url: %s, headers: %s", request.url, request.headers)
        response = await call_next(request)
        logger.debug("response will be: status: %s, headers: %s", response.status_code, response.headers)
        return response
