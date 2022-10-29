from fastapi import APIRouter

from api.routes import user


def setup(router: APIRouter):
    user.setup(router)
