import logging

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException
from fastapi.params import Body, Path

from shvatka.core.models import dto
from shvatka.core.services.user import set_password, get_user
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.api.dependencies.auth import AuthProperties

logger = logging.getLogger(__name__)


@inject
async def read_users_me(current_user: FromDishka[dto.User]) -> dto.User:
    return current_user


@inject
async def read_user(
    dao: FromDishka[HolderDao],
    id_: int = Path(alias="id"),  # type: ignore[assignment]
) -> dto.User:
    return await get_user(id_, dao.user)


@inject
async def set_password_route(
    auth: FromDishka[AuthProperties],
    user: FromDishka[dto.User],
    dao: FromDishka[HolderDao],
    password: str = Body(),  # type: ignore[assignment]
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
