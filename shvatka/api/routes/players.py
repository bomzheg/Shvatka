from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter
from fastapi.params import Path, Query

from shvatka.api.models import responses
from shvatka.core.players.interactors import GetPlayerInteractor, SearchPlayersInteractor


@inject
async def search_players(
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
async def get_player(
    interactor: FromDishka[GetPlayerInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> responses.FullPlayer:
    info = await interactor(id_)
    return responses.FullPlayer.from_core(info.player, info.team_player)


def setup() -> APIRouter:
    router = APIRouter(prefix="/players")
    router.add_api_route("/search", search_players, methods=["GET"])
    router.add_api_route("/{id}", get_player, methods=["GET"])
    return router
