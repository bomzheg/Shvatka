import logging

from fastapi import Depends, APIRouter, HTTPException
from fastapi.params import Body, Path

from shvatka.api.dependencies import get_current_user, AuthProvider, dao_provider
from shvatka.core.models import dto
from shvatka.core.services.user import set_password, get_user
from shvatka.infrastructure.db.dao.holder import HolderDao

logger = logging.getLogger(__name__)


async def read_users_me(current_user: dto.User = Depends(get_current_user)) -> dto.User:
    return current_user


async def read_user(
    id_: int = Path(alias="id"),  # type: ignore[assignment]
    dao: HolderDao = Depends(dao_provider),
) -> dto.User:
    return await get_user(id_, dao.user)


async def set_password_route(
    password: str = Body(),  # type: ignore[assignment]
    auth: AuthProvider = Depends(),
    user: dto.User = Depends(get_current_user),
    dao: HolderDao = Depends(dao_provider),
):
    hashed_password = auth.get_password_hash(password)
    await set_password(user, hashed_password, dao.user)
    raise HTTPException(status_code=200)


def setup() -> APIRouter:
    router = APIRouter(prefix="/users")
    router.add_api_route("/me", read_users_me, methods=["GET"], response_model=dto.User)
    router.add_api_route("/me/password", set_password_route, methods=["PUT"])
    router.add_api_route("/{id}", read_user, methods=["GET"])
    return router
