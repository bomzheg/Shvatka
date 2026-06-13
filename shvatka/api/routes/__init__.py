from fastapi import APIRouter

from . import team, version, auth, waivers, cdn, user, game, push, players


def setup() -> APIRouter:
    router = APIRouter()
    router.include_router(auth.setup())
    router.include_router(user.setup())
    router.include_router(game.setup())
    router.include_router(waivers.setup())
    router.include_router(team.setup())
    router.include_router(players.setup())
    router.include_router(push.setup())
    router.include_router(version.setup())
    router.include_router(cdn.setup())
    return router
