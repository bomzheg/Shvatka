from fastapi import APIRouter

from api.routes import user, game, team


def setup(router: APIRouter):
    user.setup(router)
    game.setup(router)
    team.setup(router)
