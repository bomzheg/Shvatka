from fastapi import APIRouter

from src.api.routes import team
from src.api.routes import user, game


def setup(router: APIRouter):
    user.setup(router)
    game.setup(router)
    team.setup(router)
