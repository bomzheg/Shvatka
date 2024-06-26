from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from shvatka.common import Paths
from shvatka.infrastructure.version import get_version


@inject
def get_version_route(paths: FromDishka[Paths]):
    return get_version(paths)


def setup() -> APIRouter:
    router = APIRouter()
    router.add_api_route("/version", get_version_route)
    return router
