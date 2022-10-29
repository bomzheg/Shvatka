import logging

from fastapi import Depends, APIRouter, HTTPException
from fastapi.params import Body

from api.dependencies import get_current_user, AuthProvider, dao_provider
from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.user import set_password

logger = logging.getLogger(__name__)


async def read_users_me(current_user: dto.User = Depends(get_current_user)):
    return current_user


async def set_password_route(
    password: str = Body(),
    auth: AuthProvider = Depends(),
    user: dto.User = Depends(get_current_user),
    dao: HolderDao = Depends(dao_provider)
):
    hashed_password = auth.get_password_hash(password)
    await set_password(user, hashed_password, dao.user)
    raise HTTPException(status_code=200)


def setup(router: APIRouter):
    router.add_api_route("/users/0", read_users_me, methods=["GET"], response_model=dto.User)
    router.add_api_route("/users/0/password", set_password_route, methods=["PUT"])
