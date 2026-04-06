import logging
from dataclasses import dataclass, field

import adaptix
from adaptix import Retort, name_mapping
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response

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


def sh_exception_handler(request: Request, exc: exceptions.SHError) -> Response:
    logger.error("got an sh error, during request %s", request, exc_info=exc)
    error_content = ErrorContent(
        text=exc.text,
        type=type(exc).__name__,
        description=exc.notify_user,
        properties=exc.get_properties(),
        confidential=exc.confidential,
    )
    if isinstance(exc, exceptions.NotAuthorizedForEdit):
        status_code = 403
    elif isinstance(exc, exceptions.FileNotFound):
        status_code = 404
    else:
        status_code = 422
    return JSONResponse(
        status_code=status_code,
        content=retort.dump(error_content),
    )


def setup(app: FastAPI):
    app.add_exception_handler(exceptions.SHError, sh_exception_handler)  # type: ignore[arg-type]
