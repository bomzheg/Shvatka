from fastapi import APIRouter

from shvatka.api.routes import team, version, auth
from shvatka.api.routes import user, game


def setup() -> APIRouter:
    router = APIRouter()
    router.include_router(auth.setup())
    router.include_router(user.setup())
    router.include_router(game.setup())
    router.include_router(team.setup())
    router.include_router(version.setup())
    return router
