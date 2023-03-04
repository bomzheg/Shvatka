from fastapi import APIRouter

from shvatka.api.routes import team
from shvatka.api.routes import user, game


def setup(router: APIRouter):
    user.setup(router)
    game.setup(router)
    team.setup(router)
