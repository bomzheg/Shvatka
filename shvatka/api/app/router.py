from fastapi import APIRouter

from shvatka.api.action_requests import routes as action_requests
from shvatka.api.admin import routes as admin
from shvatka.api.auth import routes as auth
from shvatka.api.docs import routes as docs
from shvatka.api.files import routes as files
from shvatka.api.games import routes as games
from shvatka.api.notifications import routes as notifications
from shvatka.api.players import routes as players
from shvatka.api.push import routes as push
from shvatka.api.search import routes as search
from shvatka.api.teams import routes as teams
from shvatka.api.version import routes as version
from shvatka.api.waivers import routes as waivers


def setup() -> APIRouter:
    router = APIRouter()
    router.include_router(auth.setup())
    router.include_router(players.setup())
    router.include_router(games.setup())
    router.include_router(waivers.setup())
    router.include_router(teams.setup())
    router.include_router(search.setup())
    router.include_router(push.setup())
    router.include_router(notifications.setup())
    router.include_router(action_requests.setup())
    router.include_router(version.setup())
    router.include_router(docs.setup())
    router.include_router(files.setup())
    router.include_router(admin.setup())
    return router
