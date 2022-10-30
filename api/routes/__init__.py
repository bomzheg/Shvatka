from fastapi import APIRouter

from api.routes import user, game


def setup(router: APIRouter):
    user.setup(router)
    game.setup(router)
