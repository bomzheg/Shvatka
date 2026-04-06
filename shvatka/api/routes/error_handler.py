import logging
from dataclasses import dataclass, field

import adaptix
from adaptix import Retort, name_mapping
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response

from shvatka.core.utils.exceptions import SHError


logger = logging.getLogger(__name__)
retort = Retort(recipe=[name_mapping(name_style=adaptix.NameStyle.CAMEL)])


@dataclass
class ErrorContent:
    type: str
    text: str = ""
    description: str = ""
    properties: dict = field(default_factory=dict)
    confidential: str | None = None


def sh_exception_handler(request: Request, exc: SHError) -> Response:
    logger.error("got an sh error, during request %s", request, exc_info=exc)
    error_content = ErrorContent(
        text=exc.text,
        type=type(exc).__name__,
        description=exc.notify_user,
        properties=exc.get_properties(),
        confidential=exc.confidential,
    )
    return JSONResponse(
        status_code=418,
        content=retort.dump(error_content),
    )


def setup(app: FastAPI):
    app.add_exception_handler(SHError, sh_exception_handler)  # type: ignore[arg-type]
