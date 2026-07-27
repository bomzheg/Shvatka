from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from shvatka.core.models import dto


@inject
def get_version_route(version: FromDishka[dto.VersionInfo]):
    return version


def setup() -> APIRouter:
    router = APIRouter()
    router.add_api_route("/version", get_version_route)
    return router
