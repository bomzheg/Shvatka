from fastapi import APIRouter

from api.routes import user


async def setup(router: APIRouter):
    user.setup(router)
