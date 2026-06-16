import logging
from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException
from fastapi.params import Body, Path, Query

from shvatka.api.models import responses
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.players.interactors import GetPlayerInteractor, SearchPlayersInteractor
from shvatka.core.players.player import set_password, set_player_username, get_player_by_id
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.api.dependencies.auth import AuthProperties

logger = logging.getLogger(__name__)


@inject
async def read_users_me(identity: FromDishka[IdentityProvider]) -> responses.Player | None:
    player_ = await identity.get_player()
    if player_ is None:
        raise HTTPException(status_code=401, detail="User not found")
    return responses.Player.from_core(player_)


@inject
async def search_users(
    interactor: FromDishka[SearchPlayersInteractor],
    username: Annotated[str | None, Query()] = None,
    name: Annotated[str | None, Query()] = None,
    active: Annotated[bool, Query()] = True,
    archive: Annotated[bool, Query()] = False,
) -> responses.Items[responses.Player]:
    players = await interactor(
        username=username,
        name=name,
        active=active,
        archive=archive,
    )
    return responses.Items([responses.Player.from_core(player) for player in players])


@inject
async def read_user(
    dao: FromDishka[HolderDao],
    id_: int = Path(alias="id"),  # type: ignore[assignment]
) -> responses.Player:
    return responses.Player.from_core(await get_player_by_id(id_, dao.player))


@inject
async def read_user_details(
    interactor: FromDishka[GetPlayerInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> responses.FullPlayer:
    info = await interactor(id_)
    return responses.FullPlayer.from_core(info.player, info.team_player)


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


@inject
async def set_username_route(
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
    username: str = Body(),  # type: ignore[assignment]
) -> None:
    player = await identity.get_required_player()
    await set_player_username(player, username, dao.player)
    raise HTTPException(status_code=200)


# users in API is players in core and db
def setup() -> APIRouter:
    router = APIRouter(prefix="/users")
    router.add_api_route("", search_users, methods=["GET"])
    router.add_api_route("/me", read_users_me, methods=["GET"])
    router.add_api_route("/me/password", set_password_route, methods=["PUT"])
    router.add_api_route("/me/username", set_username_route, methods=["PUT"])
    router.add_api_route("/{id}/details", read_user_details, methods=["GET"])
    router.add_api_route("/{id}", read_user, methods=["GET"])
    return router
