from fastapi import HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from shvatka.core.utils import exceptions


def to_http_error(
    error: exceptions.SHError,
    code: int = HTTP_500_INTERNAL_SERVER_ERROR,
) -> HTTPException:
    return HTTPException(
        status_code=code, detail={"text": error.notify_user, "description": error.text}
    )
