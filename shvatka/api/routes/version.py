from fastapi import Depends, APIRouter

from shvatka.api.config.models.main import ApiConfig
from shvatka.api.dependencies import get_config
from shvatka.infrastructure.version import get_version


def get_version_route(config: ApiConfig = Depends(get_config)):
    return get_version(config.paths)


def setup() -> APIRouter:
    router = APIRouter()
    router.add_api_route("/version", get_version_route)
    return router
