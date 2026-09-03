import logging
from dataclasses import dataclass, field
from functools import partial

import adaptix
from adaptix import Retort, name_mapping
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response

from shvatka.common.docs import DocsUrlFactory
from shvatka.core.utils import exceptions

logger = logging.getLogger(__name__)
retort = Retort(recipe=[name_mapping(name_style=adaptix.NameStyle.CAMEL)])


@dataclass
class ErrorContent:
    type: str
    text: str = ""
    description: str = ""
    properties: dict = field(default_factory=dict)
    confidential: str | None = None
    doc_url: str | None = None
    """A link to the documentation page explaining the error, for the ui to show."""


def sh_exception_handler(
    request: Request, exc: exceptions.SHError, docs: DocsUrlFactory
) -> Response:
    if not isinstance(exc, exceptions.IdentityWithoutUser | exceptions.IdentityWithoutPlayer):
        logger.error("got an sh error, during request %s", request.url, exc_info=exc)
    else:
        logger.debug("got an auth sh error, during request %s", request.url, exc_info=exc)
    error_content = ErrorContent(
        text=exc.text,
        type=type(exc).__name__,
        description=exc.notify_user,
        properties=exc.get_properties(),
        confidential=exc.confidential,
        doc_url=docs.get_error_url(exc),
    )
    if isinstance(exc, exceptions.NotAuthorizedForEdit | exceptions.NotAuthorizedForAdmin):
        status_code = 403
    elif isinstance(exc, exceptions.IdentityWithoutPlayer | exceptions.IdentityWithoutUser):
        status_code = 401
    elif isinstance(
        exc,
        exceptions.FileNotFound
        | exceptions.GameNotFound
        | exceptions.PlayerNotFoundError
        | exceptions.TeamNotFound
        | exceptions.UserNotFoundError,
    ):
        status_code = 404
    elif isinstance(exc, exceptions.FileIsUsed | exceptions.GameWouldBeRewritten):
        # a conflict the caller can resolve by asking and repeating the request
        status_code = 409
    elif isinstance(exc, exceptions.SHError):
        status_code = 422
    else:
        status_code = 500
    return JSONResponse(
        status_code=status_code,
        content=retort.dump(error_content),
        headers={
            "Cache-Control": "no-store",
        },
    )


def setup(app: FastAPI, docs: DocsUrlFactory):
    app.add_exception_handler(exceptions.SHError, partial(sh_exception_handler, docs=docs))
