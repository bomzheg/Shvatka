import logging

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException
from fastapi.params import Body, Path

from shvatka.api.models import responses
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.players.player import set_password, get_player_by_id
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.api.dependencies.auth import AuthProperties

logger = logging.getLogger(__name__)


@inject
async def read_users_me(identity: FromDishka[IdentityProvider]) -> responses.Player | None:
    return responses.Player.from_core(await identity.get_required_player())


@inject
async def read_user(
    dao: FromDishka[HolderDao],
    id_: int = Path(alias="id"),  # type: ignore[assignment]
) -> responses.Player:
    return responses.Player.from_core(await get_player_by_id(id_, dao.player))


@inject
async def set_password_route(
    auth: FromDishka[AuthProperties],
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
    password: str = Body(),  # type: ignore[assignment]
) -> None:
    hashed_password = auth.get_password_hash(password)
    await set_password(identity, hashed_password, dao.player)
    raise HTTPException(status_code=200)


# users in API is players in core and db
def setup() -> APIRouter:
    router = APIRouter(prefix="/users")
    router.add_api_route("/me", read_users_me, methods=["GET"])
    router.add_api_route("/me/password", set_password_route, methods=["PUT"])
    router.add_api_route("/{id}", read_user, methods=["GET"])
    return router
